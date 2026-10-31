"""RAM real (RSS) de cada proyecto activo del registro, como la calcula `/uso-ram`, con `psutil` (ADR-0017)."""

import os
import re
import signal
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import psutil

# pid -> (ppid, rss en KB, línea de comando)
Filas = dict[int, tuple[int, int, str]]

SCRIPT_ARRANQUE = "Script de arranque"


def leer_procesos() -> Filas:
    """Todos los procesos visibles, con `psutil` (Linux y Windows, ADR-0017)."""
    filas: Filas = {}
    for proceso in psutil.process_iter(["ppid", "memory_info", "cmdline"]):
        info = proceso.info
        memoria = info["memory_info"]
        filas[proceso.pid] = (
            info["ppid"] or 0,
            memoria.rss // 1024 if memoria else 0,
            " ".join(info["cmdline"] or []),
        )
    return filas


def descendientes(raiz: int, filas: Filas) -> set[int]:
    hijos_de: dict[int, list[int]] = {}
    for pid, (ppid, _rss, _args) in filas.items():
        hijos_de.setdefault(ppid, []).append(pid)
    visto: set[int] = set()
    pila = [raiz]
    while pila:
        pid = pila.pop()
        if pid in visto or pid not in filas:
            continue
        visto.add(pid)
        pila.extend(hijos_de.get(pid, []))
    return visto


def puertos_de(conexiones) -> dict[int, int | None]:
    """Puerto TCP en escucha -> PID, o None si es de otro usuario (sin root no se ve su PID)."""
    puertos: dict[int, int | None] = {}
    for conexion in conexiones:
        if conexion.status != psutil.CONN_LISTEN:
            continue
        if conexion.pid is not None:
            puertos[conexion.laddr.port] = conexion.pid
        else:
            # La misma escucha en IPv4 e IPv6 sale dos veces: no se pisa un PID ya visto.
            puertos.setdefault(conexion.laddr.port, None)
    return puertos


def puertos_en_escucha() -> dict[int, int | None]:
    try:
        return puertos_de(psutil.net_connections("tcp"))
    except (psutil.Error, OSError):
        return {}


def pid_en_puerto(puerto: int) -> int | None:
    # Fuente de verdad: quien esté escuchando realmente el puerto, sea quien
    # sea quien lo haya arrancado (el panel, o algo lanzado a mano antes).
    return puertos_en_escucha().get(puerto)


def _cwd(pid: int) -> str | None:
    try:
        return psutil.Process(pid).cwd()
    except psutil.Error:
        return None


def terminar(pid: int, windows: bool = os.name == "nt", espera: float = 3) -> None:
    """Para un proyecto sin `cmd_detener` (ADR-0003, ADR-0017)."""
    if not windows:
        # SIGTERM al grupo: alcanza también a los procesos que se desligaron de su padre.
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        return
    # Windows no tiene grupos de sesión: el proceso y sus hijos, y kill a los que sigan vivos.
    try:
        raiz = psutil.Process(pid)
        procesos = [raiz, *raiz.children(recursive=True)]
    except psutil.Error:
        return
    for proceso in procesos:
        try:
            proceso.terminate()
        except psutil.Error:
            pass
    _terminados, vivos = psutil.wait_procs(procesos, timeout=espera)
    for proceso in vivos:
        try:
            proceso.kill()
        except psutil.Error:
            pass


def raices_de_proceso(texto: str, filas: Filas) -> set[int]:
    """Los procesos de un proyecto sin puerto: los que llevan `texto` en su línea de comando (ADR-0017).

    Si un wrapper y el proceso que lanza lo llevan los dos, la raíz es el de más arriba.
    """
    candidatos = {pid for pid, (_ppid, _rss, args) in filas.items() if texto in args and pid != os.getpid()}
    return {pid for pid in candidatos if filas[pid][0] not in candidatos}


# Lo que puede ir delante del programa en la línea de comando: el shebang de un
# script sale como `bash ./start.sh`, y npm como `node /usr/bin/npm run dev`.
INTERPRETES = {"sh", "bash", "dash", "zsh", "node", "python", "python3"}


def _nombre(ruta: str) -> str:
    # Último componente con `/` o `\` (Windows), sin `.exe`: `C:\Python\python.exe` es `python`.
    nombre = re.split(r"[\\/]", ruta)[-1]
    return nombre[:-4] if nombre.lower().endswith(".exe") else nombre


def _ejecuta(cmd: list[str], args: str) -> bool:
    """Si la línea de comando lanza `cmd`: su programa al principio o tras un intérprete, y sus argumentos detrás.

    Así `vim start.sh` o `npm install` en la misma carpeta no pasan por `./start.sh` o `npm run dev`.
    """
    programa = _nombre(cmd[0])
    palabras = args.split()
    nombres = [_nombre(palabra) for palabra in palabras]
    return any(
        nombre == programa and (i == 0 or nombres[i - 1] in INTERPRETES) and palabras[i + 1 : i + len(cmd)] == cmd[1:]
        for i, nombre in enumerate(nombres)
    )


def raices_reales(cmd: list[str], path: Path, filas: Filas, cwd_de: Callable[[int], str | None] = _cwd) -> set[int]:
    """Los procesos que ejecutan `cmd` en `path`, los haya lanzado el panel o una terminal.

    Se busca por comando y `cwd`, no por parentesco con el launcher: varios proyectos
    comparten `./start.sh` y solo el directorio los distingue. Si el script corre dos
    veces, cuentan las dos instancias.
    """
    destino = os.path.realpath(path)
    candidatos = set()
    for pid, (_ppid, _rss, args) in filas.items():
        if _ejecuta(cmd, args):
            cwd = cwd_de(pid)
            if cwd is not None and os.path.realpath(cwd) == destino:
                candidatos.add(pid)
    # Si el script se relanza a sí mismo (bash -> bash), la raíz es el de más arriba.
    return {pid for pid in candidatos if filas[pid][0] not in candidatos}


def _kb(pids: set[int], filas: Filas) -> int:
    return sum(filas[pid][1] for pid in pids if pid in filas)


def _medir_proyecto(proyecto: dict, filas: Filas, puertos: dict[int, int | None], cwd_de) -> dict | None:
    if proyecto["puerto"] is None and proyecto.get("proceso"):
        raices = raices_de_proceso(proyecto["proceso"], filas)
        if not raices:
            return None
        pids = set().union(*(descendientes(raiz, filas) for raiz in raices))
        return {"nombre": proyecto["nombre"], "puerto": None, "pids": pids, "kb": _kb(pids, filas), "desglose": []}
    # Sin puerto principal (el stack de negocios), cuenta como activo si escucha cualquiera de sus servicios.
    puertos_estado = (
        [proyecto["puerto"]]
        if proyecto["puerto"] is not None
        else [puerto for _etiqueta, puerto, _ruta, _host in proyecto.get("enlaces", [])]
    )
    escuchando = [puerto for puerto in puertos_estado if puerto in puertos]
    if not escuchando:
        return None
    pid_principal = puertos[escuchando[0]]
    if all(puertos[puerto] is None for puerto in escuchando):
        # Activo, pero el proceso es de otro usuario (Docker como root): su RAM no se ve.
        return {"nombre": proyecto["nombre"], "puerto": proyecto["puerto"], "pids": set(), "kb": None, "desglose": []}
    if proyecto["cmd"] is None:
        # Esta app: sus hijos son los otros proyectos que arrancó, que ya se cuentan aparte.
        pids = {pid_principal}
    else:
        # Unión de los dos caminos: los wrappers (pnpm dev -> next dev) quedan por encima
        # del proceso del puerto, y algunos servicios se reparentan fuera de la raíz.
        pids = set()
        for raiz in raices_reales(proyecto["cmd"], proyecto["path"], filas, cwd_de):
            pids |= descendientes(raiz, filas)
        puertos_raiz = {puerto for _etiqueta, puerto, _ruta, _host in proyecto.get("enlaces", [])}
        for puerto in puertos_raiz or {proyecto["puerto"]}:
            pid = puertos.get(puerto)
            if pid is not None:
                pids |= descendientes(pid, filas)

    desglose = []
    if proyecto.get("enlaces"):
        asignados: set[int] = set()
        # Un puerto en varios enlaces (la app y su admin en otro host) es un solo servicio:
        # va con el primer enlace que lo nombra.
        vistos: set[int] = set()
        for etiqueta, puerto, _ruta, _host in proyecto["enlaces"]:
            if puerto in vistos:
                continue
            vistos.add(puerto)
            pid = puertos.get(puerto)
            servicio = (descendientes(pid, filas) & pids) - asignados if pid is not None else set()
            asignados |= servicio
            desglose.append((etiqueta, puerto, _kb(servicio, filas)))
        resto = pids - asignados
        if resto:
            desglose.append((SCRIPT_ARRANQUE, None, _kb(resto, filas)))
    return {
        "nombre": proyecto["nombre"],
        "puerto": proyecto["puerto"],
        "pids": pids,
        "kb": _kb(pids, filas),
        "desglose": desglose,
    }


def medir(proyectos: list[dict], filas: Filas, puertos: dict[int, int | None], cwd_de=_cwd) -> dict:
    """`{"proyectos": [...], "compartidos": [(nombre, nombre)]}`, de mayor a menor consumo.

    `puertos` es la salida de `puertos_de`. Solo cuenta los proyectos con algo escuchando
    en su puerto principal (o, si no tienen, en el de algún enlace) o, sin puerto, con un
    proceso que lleve su `proceso`; los de otro usuario
    van al final con `kb` None. `compartidos`
    lista los pares con PIDs en común: si no está vacío, se ha contado RAM dos veces.
    """
    medidos = [m for p in proyectos if (m := _medir_proyecto(p, filas, puertos, cwd_de))]
    compartidos = [
        (a["nombre"], b["nombre"]) for i, a in enumerate(medidos) for b in medidos[i + 1 :] if a["pids"] & b["pids"]
    ]
    return {
        "proyectos": sorted(medidos, key=lambda m: -1 if m["kb"] is None else m["kb"], reverse=True),
        "compartidos": compartidos,
    }


def fila_heruka_flow(
    negocios: list[dict],
    ruta: Path,
    single: dict,
    nombre: str = "Todos los negocios",
    negocio: str = "Negocio {id}",
    backend: str = "Backend común",
) -> dict:
    """La fila de heruka-flow: el stack multi-tenant si hay `negocios` (de `--listar`), si no el single.

    Los dos modos se excluyen (ADR-0005), así que nunca hay dos filas con los mismos procesos.
    El stack no tiene puerto principal: sus raíces son `dev_up.sh` y los servicios de cada negocio.
    Las APIs de todos los negocios las sirve un mismo proceso, el backend común: va en una
    sola línea, con el puerto de la primera API, en vez de repartido entre negocios.
    """
    if not negocios:
        return single
    return {
        "nombre": nombre,
        "slug": "negocios",
        "puerto": None,
        "path": ruta,
        "cmd": ["./scripts/dev_up.sh"],
        "enlaces": [
            *(
                (f"{negocio.format(id=n['id'])} · {servicio}", n[parte], "", "localhost")
                for n in negocios
                for parte, servicio in (("front", "Frontend"), ("panel", "Panel"))
            ),
            (backend, negocios[0]["api"], "", "localhost"),
        ],
    }


def consultar(proyectos: list[dict]) -> dict:
    """Lee procesos y puertos una vez y mide: `{"medicion", "hora", "error"}`; `error` es None si fue bien."""
    try:
        filas = leer_procesos()
    except (psutil.Error, OSError) as e:
        return {"medicion": None, "hora": datetime.now(), "error": str(e)}
    return {"medicion": medir(proyectos, filas, puertos_en_escucha()), "hora": datetime.now(), "error": None}


def formatear(kb: int) -> str:
    mb = kb / 1024
    texto = f"{mb / 1024:.2f} GB" if mb >= 1024 else f"{mb:.0f} MB"
    return texto.replace(".", ",")


def memoria_total_kb() -> int | None:
    """RAM total de la máquina, para poner el total de los proyectos en contexto."""
    try:
        return psutil.virtual_memory().total // 1024
    except (psutil.Error, OSError):
        return None

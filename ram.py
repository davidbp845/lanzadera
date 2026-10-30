"""RAM real (RSS) de cada proyecto activo del registro, como la calcula `/uso-ram`."""

import os
import re
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

# pid -> (ppid, rss en KB, línea de comando)
Filas = dict[int, tuple[int, int, str]]

SCRIPT_ARRANQUE = "Script de arranque"


def parsear_ps(salida: str) -> Filas:
    """Lee la salida de `ps -eo pid=,ppid=,rss=,args=`."""
    filas: Filas = {}
    for linea in salida.splitlines():
        partes = linea.split(None, 3)
        if len(partes) < 3:
            continue
        pid, ppid, rss = (int(p) for p in partes[:3])
        filas[pid] = (ppid, rss, partes[3] if len(partes) == 4 else "")
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


def parsear_ss(salida: str) -> dict[int, int | None]:
    """Lee `ss -H -ltnp`: puerto en escucha -> PID, o None si es de otro usuario.

    Sin root, `ss` lista los puertos de root (docker-proxy) pero no dice su PID.
    """
    puertos: dict[int, int | None] = {}
    for linea in salida.splitlines():
        campos = linea.split()
        if len(campos) < 4:
            continue
        puerto = int(campos[3].rsplit(":", 1)[1])
        coincidencia = re.search(r"pid=(\d+)", linea)
        if coincidencia:
            puertos[puerto] = int(coincidencia.group(1))
        else:
            # La misma escucha en IPv4 e IPv6 sale dos veces: no se pisa un PID ya visto.
            puertos.setdefault(puerto, None)
    return puertos


def _ss(*filtro: str) -> dict[int, int | None]:
    try:
        salida = subprocess.run(
            ["ss", "-H", "-ltnp", *filtro], check=False, capture_output=True, text=True, timeout=1
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return parsear_ss(salida)


def pid_en_puerto(puerto: int) -> int | None:
    # Fuente de verdad: quien esté escuchando realmente el puerto, sea quien
    # sea quien lo haya arrancado (el panel, o algo lanzado a mano antes).
    return _ss(f"sport = :{puerto}").get(puerto)


def _cwd(pid: int) -> str | None:
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None


# Lo que puede ir delante del programa en la línea de comando: el shebang de un
# script sale como `bash ./start.sh`, y npm como `node /usr/bin/npm run dev`.
INTERPRETES = {"sh", "bash", "dash", "zsh", "node", "python", "python3"}


def _ejecuta(cmd: list[str], args: str) -> bool:
    """Si la línea de comando lanza `cmd`: su programa al principio o tras un intérprete, y sus argumentos detrás.

    Así `vim start.sh` o `npm install` en la misma carpeta no pasan por `./start.sh` o `npm run dev`.
    """
    programa = cmd[0].rsplit("/", 1)[-1]
    palabras = args.split()
    nombres = [palabra.rsplit("/", 1)[-1] for palabra in palabras]
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

    `puertos` es la salida de `parsear_ss`. Solo cuenta los proyectos con algo escuchando
    en su puerto principal (o, si no tienen, en el de algún enlace); los de otro usuario
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
    """Lee `ps` y `ss` una vez cada uno y mide: `{"medicion", "hora", "error"}`; `error` es None si fue bien."""
    try:
        salida = subprocess.run(
            ["ps", "-eo", "pid=,ppid=,rss=,args="], capture_output=True, text=True, check=True, timeout=5
        ).stdout
    except (OSError, subprocess.SubprocessError) as e:
        return {"medicion": None, "hora": datetime.now(), "error": str(e)}
    return {"medicion": medir(proyectos, parsear_ps(salida), _ss()), "hora": datetime.now(), "error": None}


def formatear(kb: int) -> str:
    mb = kb / 1024
    texto = f"{mb / 1024:.2f} GB" if mb >= 1024 else f"{mb:.0f} MB"
    return texto.replace(".", ",")


def memoria_total_kb(meminfo: Path = Path("/proc/meminfo")) -> int | None:
    """RAM total de la máquina (`MemTotal`), para poner el total de los proyectos en contexto."""
    try:
        for linea in meminfo.read_text().splitlines():
            if linea.startswith("MemTotal:"):
                return int(linea.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None

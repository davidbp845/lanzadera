"""Consulta el estado de un VPS por SSH y lo trocea en secciones (ADR-0008)."""

import subprocess
import time
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "scripts" / "estado_vps.sh"
MARCA = "### "
TIMEOUT = 15
# Filas de la página VPS, de las salidas cortas a las anchas, para que todo quepa
# en una pantalla de 1920×1080 sin scroll.
FILAS = [
    ["Sistema", "Memoria", "Servicios con fallo"],
    ["Disco", "Procesos con más RAM"],
    ["Contenedores", "Últimos accesos"],
]


def trocear(salida: str) -> list[tuple[str, str]]:
    """Parte la salida de `estado_vps.sh` en `(título, texto)` por sus líneas `### <Sección>`."""
    secciones: list[tuple[str, list[str]]] = []
    for linea in salida.splitlines():
        if linea.startswith(MARCA):
            secciones.append((linea.removeprefix(MARCA).strip(), []))
        elif secciones:
            secciones[-1][1].append(linea)
    # Solo se quitan saltos de línea: los espacios iniciales alinean las columnas (ps, free).
    return [(titulo, "\n".join(lineas).strip("\n")) for titulo, lineas in secciones]


def repartir(secciones: list[tuple[str, str]]) -> list[list[tuple[str, str] | None]]:
    """Coloca las secciones en `FILAS` por título.

    Una sección que el servidor no imprimió deja su hueco (`None`) para no descuadrar
    la rejilla; las filas sin ninguna se omiten. Las que no están en `FILAS` van al final.
    """
    por_titulo = dict(secciones)
    filas = [[(t, por_titulo[t]) if t in por_titulo else None for t in fila] for fila in FILAS]
    filas = [fila for fila in filas if any(fila)]
    conocidos = {t for fila in FILAS for t in fila}
    sobrantes = [s for s in secciones if s[0] not in conocidos]
    filas += [sobrantes[i : i + 3] for i in range(0, len(sobrantes), 3)]
    return filas


_UNIDADES = {"B": 1, "K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40, "P": 2**50}


def _bytes(texto: str) -> float | None:
    """`3.8Gi` / `412Mi` / `21G` (de `free -h` o `df -h`, con coma o punto) -> bytes."""
    texto = texto.replace(",", ".").removesuffix("i")
    try:
        return float(texto[:-1]) * _UNIDADES[texto[-1].upper()] if texto[-1].isalpha() else float(texto)
    except (ValueError, KeyError, IndexError):
        return None


def medidores(secciones: list[tuple[str, str]]) -> dict:
    """Lo que pintan los medidores de la página VPS, leído de las mismas secciones que se muestran.

    `{"memoria": (usado, total, disponible) | None, "disco": (porcentaje, usado, tamaño) | None,
    "carga": (carga a 1 min, nº de CPU) | None, "fallos": int | None}`. Lo que no se pueda leer, None.
    """
    por_titulo = dict(secciones)
    resultado: dict = {"memoria": None, "disco": None, "carga": None, "fallos": None}

    for linea in por_titulo.get("Memoria", "").splitlines():
        campos = linea.split()
        if campos and campos[0] == "Mem:" and len(campos) >= 5:
            # Columnas de estado_vps.sh: total, used, free, available.
            total, usado, disponible = _bytes(campos[1]), _bytes(campos[2]), _bytes(campos[4])
            if total and usado is not None:
                resultado["memoria"] = (usado, total, disponible)

    for linea in por_titulo.get("Disco", "").splitlines():
        campos = linea.split()
        if len(campos) >= 6 and campos[-1] == "/" and campos[-2].endswith("%"):
            resultado["disco"] = (int(campos[-2].rstrip("%")), campos[2], campos[1])

    for linea in por_titulo.get("Sistema", "").splitlines():
        campos = linea.split()
        # "carga" en estado_vps.sh; "load" en la salida de ejemplo de la demo.
        if len(campos) >= 2 and campos[0] in {"carga", "load"} and "CPU)" in linea:
            try:
                resultado["carga"] = (float(campos[1].replace(",", ".")), int(linea.rsplit("(", 1)[1].split()[0]))
            except (ValueError, IndexError):
                pass

    if "Servicios con fallo" in por_titulo:
        texto = por_titulo["Servicios con fallo"].strip()
        # Sin fallos, el script imprime "0 servicios con fallo"; con fallos, una línea por servicio.
        resultado["fallos"] = 0 if not texto or texto.startswith("0 ") else len(texto.splitlines())
    return resultado


def consultar(host: str) -> dict:
    """Una llamada SSH: `{"secciones", "hora", "duracion", "error"}`; `error` es None si fue bien."""
    inicio = time.monotonic()
    secciones: list[tuple[str, str]] = []
    try:
        # BatchMode: si la clave no basta, falla en vez de esperar una contraseña
        # o la confirmación de una huella que nadie va a teclear desde el panel.
        resultado = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", host, "sh", "-s"],
            input=SCRIPT.read_text(encoding="utf-8"),
            capture_output=True,
            encoding="utf-8",
            timeout=TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        error = f"Sin respuesta de {host} en {TIMEOUT} s"
    except OSError as e:
        error = str(e)
    else:
        if resultado.returncode != 0:
            error = resultado.stderr.strip() or f"ssh terminó con código {resultado.returncode}"
        else:
            error = None
            secciones = trocear(resultado.stdout)
    return {"secciones": secciones, "hora": datetime.now(), "duracion": time.monotonic() - inicio, "error": error}

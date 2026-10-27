"""Commits por día de todos los proyectos del registro, para el mapa de actividad de la Lanzadera.

Solo lee: `git log` local en cada repositorio, sin red.
"""

import subprocess
from collections import Counter
from datetime import date
from pathlib import Path


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=5, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def repositorios(carpetas: list[Path]) -> set[Path]:
    """La raíz git de cada carpeta y de sus submódulos, sin repetir (contenedor y submódulo cuentan los dos)."""
    raices = set()
    for carpeta in carpetas:
        if not carpeta.is_dir():
            continue
        if raiz := _git("-C", str(carpeta), "rev-parse", "--show-toplevel").strip():
            raices.add(Path(raiz))
        rutas = _git("config", "-f", str(carpeta / ".gitmodules"), "--get-regexp", r"^submodule\..*\.path$")
        raices |= {
            carpeta / linea.split()[-1] for linea in rutas.splitlines() if (carpeta / linea.split()[-1]).is_dir()
        }
    return raices


def contar(fechas: str) -> Counter[date]:
    """Lee una fecha `AAAA-MM-DD` por línea (`git log --format=%cs`)."""
    return Counter(date.fromisoformat(linea) for linea in fechas.split() if linea)


def commits_por_dia(repos: set[Path], desde: date, hasta: date) -> dict[date, int]:
    """Commits de todas las ramas, por fecha de commit, de `desde` a `hasta` (los días sin commits, a cero)."""
    total: Counter[date] = Counter()
    for repo in repos:
        total += contar(_git("-C", str(repo), "log", "--all", f"--since={desde.isoformat()}", "--format=%cs"))
    return {date.fromordinal(d): total[date.fromordinal(d)] for d in range(desde.toordinal(), hasta.toordinal() + 1)}

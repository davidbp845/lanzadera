"""Prioridad de cada fila de la Lanzadera en `prioridades.toml`, que solo escribe el panel (ADR-0023)."""

import json
import tomllib
from pathlib import Path

MINIMA, MAXIMA = 1, 5
CABECERA = "# Prioridad de cada fila de la Lanzadera (1 a 5, 5 lo más prioritario). La escribe el panel.\n"


def cargar(ruta: Path) -> dict[str, int]:
    """`slug -> prioridad`; sin fichero, vacío. Un valor que no es un entero de 1 a 5 se ignora."""
    if not ruta.exists():
        return {}
    datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    # bool es un int en Python: `true` no es una prioridad.
    return {
        slug: valor
        for slug, valor in datos.items()
        if isinstance(valor, int) and not isinstance(valor, bool) and MINIMA <= valor <= MAXIMA
    }


def guardar(ruta: Path, prioridades: dict[str, int]) -> None:
    # Claves entre comillas (un slug puede no ser una clave TOML suelta) y ordenadas, para que el diff
    # de cada clic sea una sola línea.
    lineas = [f"{json.dumps(slug, ensure_ascii=False)} = {valor}\n" for slug, valor in sorted(prioridades.items())]
    ruta.write_text(CABECERA + "".join(lineas), encoding="utf-8")


def cambiar(prioridades: dict[str, int], slug: str, paso: int) -> dict[str, int]:
    """Sube o baja una unidad, dentro de 1–5; sin prioridad, subir la pone en 1 y bajar no hace nada."""
    actual = prioridades.get(slug)
    if actual is None:
        nueva = MINIMA if paso > 0 else None
    else:
        nueva = min(max(actual + paso, MINIMA), MAXIMA)
    return prioridades if nueva is None else {**prioridades, slug: nueva}

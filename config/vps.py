"""Carga los servidores de la página VPS (`datos/vps.toml`, ADR-0008)."""

import tomllib
from pathlib import Path

from config import paths


def cargar(fichero: Path | None = None) -> list[dict]:
    """Devuelve `[{"nombre", "host"}, ...]`; sin fichero, una lista vacía (la página explica cómo añadirlo)."""
    fichero = fichero or paths.vps()
    if not fichero.exists():
        return []
    with fichero.open("rb") as f:
        return tomllib.load(f).get("vps", [])

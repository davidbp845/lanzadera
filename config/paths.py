"""Rutas a los datos, que viven fuera de este repo, en el contenedor (ADR-0001)."""

import os
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
# Datos ficticios de la demo pública, versionados en este repo (ADR-0010).
DEMO = RAIZ_REPO / "demo"
IDIOMAS = ("es", "en")


def demo() -> bool:
    """`HOME_LAUNCHER_DEMO=1`: solo lectura, con los datos de `demo/` en vez de consultar el sistema."""
    return os.environ.get("HOME_LAUNCHER_DEMO") == "1"


def idioma() -> str:
    """Idioma inicial del panel: `HOME_LAUNCHER_IDIOMA` (`es`/`en`); si no, inglés en la demo y español fuera."""
    valor = os.environ.get("HOME_LAUNCHER_IDIOMA", "")
    return valor if valor in IDIOMAS else ("en" if demo() else "es")


def datos() -> Path:
    """`HOME_LAUNCHER_DATOS` si está definida; si no, `demo/` en la demo o `../datos` respecto a la raíz del repo."""
    return Path(os.environ.get("HOME_LAUNCHER_DATOS") or (DEMO if demo() else RAIZ_REPO.parent / "datos"))


def raiz_data() -> Path:
    """Carpeta Data, contra la que se resuelven las rutas de `proyectos.toml`.

    `HOME_LAUNCHER_RAIZ` si está definida; si no, `demo/` en la demo (las rutas son ficticias
    y no se leen) o tres niveles por encima del repo (`Data/Apps/home/home`).
    """
    return Path(os.environ.get("HOME_LAUNCHER_RAIZ") or (DEMO if demo() else RAIZ_REPO.parents[2]))


def proyectos() -> Path:
    return datos() / "proyectos.toml"


def enlaces() -> Path:
    return datos() / "enlaces.csv"


def vps() -> Path:
    return datos() / "vps.toml"

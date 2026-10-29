"""Carga el registro de proyectos (`datos/proyectos.toml`) en los dicts que usa el launcher."""

import tomllib
from pathlib import Path

from config import paths


def _proyecto(entrada: dict, raiz: Path) -> dict:
    # Sin puerto, el proyecto no tiene app: su fila es solo de enlaces de GitHub (ADR-0014).
    proyecto = {
        **entrada,
        "path": raiz / entrada["ruta"],
        "cmd": entrada.get("cmd"),
        "puerto": entrada.get("puerto"),
        "tipo": entrada.get("tipo"),
    }
    if "enlaces" in entrada:
        # (etiqueta, puerto, ruta_url, host): la forma que pintan los enlaces de la UI.
        proyecto["enlaces"] = [
            (e["etiqueta"], e["puerto"], e.get("ruta_url", ""), e.get("host", "localhost")) for e in entrada["enlaces"]
        ]
    return proyecto


def url_enlace(enlace: tuple[str, int, str, str]) -> str:
    """URL que abre el navegador. El host solo cambia esto: el estado sale siempre del puerto local."""
    _etiqueta, puerto, ruta_url, host = enlace
    return f"http://{host}:{puerto}{ruta_url}"


def cargar(fichero: Path | None = None, raiz: Path | None = None) -> dict:
    """Devuelve `{"proyectos": [...], "heruka_flow": Path, "intentos_negocios": int, "heruka_life_single": dict}`.

    `[negocios]` es opcional (solo tiene sentido con heruka-flow): sin ella, `heruka_flow` y
    `heruka_life_single` son `None`.
    """
    fichero = fichero or paths.proyectos()
    raiz = raiz or paths.raiz_data()
    with fichero.open("rb") as f:
        registro = tomllib.load(f)
    negocios = registro.get("negocios")
    return {
        "proyectos": [_proyecto(p, raiz) for p in registro["proyecto"]],
        "heruka_flow": raiz / negocios["ruta"] if negocios else None,
        "intentos_negocios": negocios.get("intentos_espera_inicio", 20) if negocios else 20,
        "heruka_life_single": _proyecto(negocios["single"], raiz) if negocios else None,
    }

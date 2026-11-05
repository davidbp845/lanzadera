"""Carga el registro de proyectos (`datos/proyectos.toml`) en los dicts que usa el launcher."""

import tomllib
from pathlib import Path

from config import paths


def _carpeta_github(entrada: dict, raiz: Path) -> Path | None:
    ruta_github = entrada.get("ruta_github", entrada["ruta"])
    return raiz / ruta_github if ruta_github is not False else None


def _proyecto(entrada: dict, raiz: Path) -> dict:
    # Sin puerto ni proceso, el proyecto no tiene app: su fila es solo de enlaces de GitHub (ADR-0014).
    # Sin puerto pero con proceso, su estado sale de la línea de comando de sus procesos (ADR-0017).
    proyecto = {
        **entrada,
        "path": raiz / entrada["ruta"],
        # Repositorio y tablero: los de `ruta_github` si el proyecto se arranca desde el código de otro;
        # con `false`, ninguno: es parte de ese otro proyecto y su GitHub ya sale en su fila (ADR-0021).
        "path_github": _carpeta_github(entrada, raiz),
        "cmd": entrada.get("cmd"),
        "puerto": entrada.get("puerto"),
        "proceso": entrada.get("proceso"),
        "tipo": entrada.get("tipo"),
    }
    if "enlaces" in entrada:
        # (etiqueta, puerto, ruta_url, host, tipo): la forma que pintan los enlaces de la UI. Un enlace
        # sin tipo hereda el de su fila, que en las de negocios lo pone el código: aquí queda en None (ADR-0022).
        proyecto["enlaces"] = [
            (e["etiqueta"], e["puerto"], e.get("ruta_url", ""), e.get("host", "localhost"), e.get("tipo"))
            for e in entrada["enlaces"]
        ]
    return proyecto


def url_enlace(enlace: tuple[str, int, str, str, str | None]) -> str:
    """URL que abre el navegador. El host solo cambia esto: el estado sale siempre del puerto local."""
    _etiqueta, puerto, ruta_url, host, _tipo = enlace
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

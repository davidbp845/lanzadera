"""Página Claude (issue #13): maqueta con una conversación de ejemplo.

Todavía no llama al Claude Agent SDK. La conversación sale de aquí, como la que enseñará la demo
(ADR-0010), que no puede ejecutar nada.

Cada mensaje es un dict con `rol`:
- `usuario`: lo que se pide (`texto`).
- `claude`: la respuesta (`texto`) y los pasos intermedios que no se enseñan salvo que se abran (`pasos`).
- `pregunta`: una `AskUserQuestion` (`cabecera`, `pregunta`, `opciones` como `(etiqueta, descripción)`).
- `permiso`: una petición de permiso (`herramienta`, `detalle`).
"""

CONVERSACION = {
    "es": [
        {"rol": "usuario", "texto": "¿Pasan los tests de este proyecto?"},
        {
            "rol": "claude",
            "pasos": ["Leer `pyproject.toml`", "Ejecutar `./venv/bin/pytest`", "Leer `tests/test_ram.py`"],
            "texto": (
                "Pasan **41 de 42**. Falla `test_ram_total`: espera la RAM en MB y `ram.py` la devuelve en kB "
                "desde el último cambio."
            ),
        },
        {"rol": "usuario", "texto": "Arréglalo"},
        {
            "rol": "pregunta",
            "cabecera": "Corrección",
            "pregunta": "¿Dónde corrijo la unidad?",
            "opciones": [
                ("En ram.py (recomendado)", "La página Local ya espera MB; el test tiene razón."),
                ("En el test", "Se acepta kB como unidad y se actualiza la expectativa."),
            ],
        },
        {"rol": "permiso", "herramienta": "Edit", "detalle": "ram.py"},
        {
            "rol": "claude",
            "pasos": ["Editar `ram.py`", "Ejecutar `./venv/bin/pytest`", "Ejecutar `./venv/bin/ruff check .`"],
            "texto": "Hecho: `ram.py` vuelve a devolver MB. Pasan los **42** tests y ruff no da avisos.",
        },
    ],
    "en": [
        {"rol": "usuario", "texto": "Do this project's tests pass?"},
        {
            "rol": "claude",
            "pasos": ["Read `pyproject.toml`", "Run `./venv/bin/pytest`", "Read `tests/test_ram.py`"],
            "texto": (
                "**41 of 42** pass. `test_ram_total` fails: it expects RAM in MB and `ram.py` returns kB "
                "since the last change."
            ),
        },
        {"rol": "usuario", "texto": "Fix it"},
        {
            "rol": "pregunta",
            "cabecera": "Fix",
            "pregunta": "Where should I fix the unit?",
            "opciones": [
                ("In ram.py (recommended)", "The Local page already expects MB; the test is right."),
                ("In the test", "Accept kB as the unit and update the expectation."),
            ],
        },
        {"rol": "permiso", "herramienta": "Edit", "detalle": "ram.py"},
        {
            "rol": "claude",
            "pasos": ["Edit `ram.py`", "Run `./venv/bin/pytest`", "Run `./venv/bin/ruff check .`"],
            "texto": "Done: `ram.py` returns MB again. All **42** tests pass and ruff reports nothing.",
        },
    ],
}


def sugerencias(activo: bool | None, tablero: dict | None, idioma: str) -> list[str]:
    """Peticiones de partida según lo que la Lanzadera ya sabe del proyecto."""
    es = idioma == "es"
    lista = []
    if activo is False:
        lista.append("¿Por qué no arranca?" if es else "Why doesn't it start?")
    if tablero and tablero.get("Ready"):
        lista.append("/dev:sprint")
    if tablero and tablero.get("In review"):
        lista.append("Resume lo que hay en In review" if es else "Summarise what's in In review")
    lista.append("¿Pasan los tests?" if es else "Do the tests pass?")
    return lista

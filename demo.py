"""Datos de ejemplo del modo demo (ADR-0010).

Sustituyen a todo lo que el launcher consulta del sistema (puertos, `ps`/`ss`, `gh`,
`git log`, `dev_up.sh --listar`, SSH al VPS): en la demo no se ejecuta nada.
"""

import random
import tomllib
from datetime import date, datetime, timedelta
from functools import cache

import github
import vps
from config import paths

ESTADO = paths.DEMO / "estado.toml"
SALIDA_VPS = paths.DEMO / "vps.txt"
# Dueño ficticio de los tableros: el número es la posición del proyecto en `[github]`.
OWNER = "demo"


@cache
def _estado() -> dict:
    with ESTADO.open("rb") as f:
        return tomllib.load(f)


def puerto_activo(puerto: int) -> bool:
    return puerto in _estado()["activos"]


def memoria_total_kb() -> int:
    return _estado()["memoria_total_gb"] * 1024 * 1024


def listar_negocios() -> list[dict]:
    return [dict(n) for n in _estado()["negocios"]]


def repositorio_y_tablero(slug: str) -> tuple[str | None, tuple[str, int] | None]:
    """`(repositorio, (owner, número))` del proyecto, como `github.repositorio` y `github.tablero_id`."""
    slugs = list(_estado()["github"])
    if slug not in slugs:
        return None, None
    return _estado()["github"][slug]["repo"], (OWNER, slugs.index(slug) + 1)


def recuento(owner: str, numero: int) -> dict | None:
    """La misma forma que `github.recuento`."""
    entradas = list(_estado()["github"].values())
    if owner != OWNER or not 1 <= numero <= len(entradas):
        return None
    entrada = entradas[numero - 1]
    return {**dict(zip(github.ESTADOS, entrada["cuenta"], strict=True)), "en_curso": entrada.get("en_curso", [])}


def ram(proyectos: list[dict]) -> dict:
    """La misma forma que `ram.consultar`, con la RAM de `[ram]` de los proyectos activos."""
    medidos = []
    for proyecto in proyectos:
        servicios = _estado()["ram"].get(proyecto["slug"])
        # Sin puerto principal (los negocios), basta con que escuche alguno de sus servicios.
        puertos = (
            [proyecto["puerto"]] if proyecto["puerto"] is not None else [e[1] for e in proyecto.get("enlaces", [])]
        )
        if not servicios or not any(puerto_activo(p) for p in puertos):
            continue
        desglose = [(s["etiqueta"], s.get("puerto"), s["mb"] * 1024) for s in servicios]
        medidos.append(
            {
                "nombre": proyecto["nombre"],
                "puerto": proyecto["puerto"],
                "pids": set(),
                "kb": sum(kb for *_resto, kb in desglose),
                "desglose": desglose if len(desglose) > 1 else [],
            }
        )
    medidos.sort(key=lambda m: m["kb"], reverse=True)
    return {"medicion": {"proyectos": medidos, "compartidos": []}, "hora": datetime.now(), "error": None}


def consultar_vps(_host: str) -> dict:
    """La misma forma que `vps.consultar`, con la salida guardada en `demo/vps.txt`."""
    return {
        "secciones": vps.trocear(SALIDA_VPS.read_text(encoding="utf-8")),
        "hora": datetime.now(),
        "duracion": 1.4,
        "error": None,
    }


def actividad(desde: date, hasta: date) -> dict[date, int]:
    """Commits por día, inventados pero siempre los mismos para el mismo día: más entre semana."""
    commits = {}
    dia = desde
    while dia <= hasta:
        azar = random.Random(dia.toordinal())
        fin_de_semana = dia.weekday() >= 5
        commits[dia] = 0 if fin_de_semana and azar.random() < 0.6 else azar.choice([0, 0, 0, 1, 1, 2, 3, 5, 8, 13])
        dia += timedelta(days=1)
    return commits

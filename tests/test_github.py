import json
import subprocess
from pathlib import Path

import pytest

import github


def _git(carpeta: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(carpeta), *args], check=True, capture_output=True)


@pytest.mark.parametrize(
    ("remoto", "url"),
    [
        ("git@github.com:davidbp845/lanzadera.git", "https://github.com/davidbp845/lanzadera"),
        ("https://github.com/davidbp845/lanzadera.git\n", "https://github.com/davidbp845/lanzadera"),
        ("ssh://git@github.com/davidbp845/lanzadera", "https://github.com/davidbp845/lanzadera"),
        ("/srv/git/local.git", None),
    ],
)
def test_url_web(remoto, url):
    assert github.url_web(remoto) == url


def test_repositorio_del_origin_o_del_primer_submodulo(tmp_path):
    con_remoto, contenedor, sin_git = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    for carpeta in (con_remoto, contenedor, sin_git):
        carpeta.mkdir()
    _git(con_remoto, "init", "-q")
    _git(con_remoto, "remote", "add", "origin", "git@github.com:o/a.git")
    _git(contenedor, "init", "-q")
    (contenedor / ".gitmodules").write_text('[submodule "b"]\n\tpath = b\n\turl = https://github.com/o/b-app.git\n')
    assert github.repositorio(con_remoto) == "https://github.com/o/a"
    assert github.repositorio(contenedor) == "https://github.com/o/b-app"
    assert github.repositorio(sin_git) is None
    assert github.repositorio(tmp_path / "no-existe") is None


METODO = '# P\n\n## Método\n\n- Tipo: dev\n- Tablero: proyecto GitHub "P" (owner `davidbp845`, número `9`)\n'


@pytest.mark.parametrize(
    ("claude_md", "esperado"),
    [
        (METODO, "https://github.com/users/davidbp845/projects/9"),
        ("# P\n\n## Método\n\n- Tipo: dev\n", None),
        ("# Sin método\n", None),
    ],
)
def test_tablero_del_claude_md_mas_cercano(tmp_path, claude_md, esperado):
    codigo = tmp_path / "Apps/p/p"
    codigo.mkdir(parents=True)
    (tmp_path / "Apps/p/CLAUDE.md").write_text(claude_md)
    assert github.tablero(codigo, tmp_path) == esperado


def test_tablero_no_sube_por_encima_de_la_raiz(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(METODO)
    raiz = tmp_path / "Data"
    (raiz / "Apps/p").mkdir(parents=True)
    assert github.tablero(raiz / "Apps/p", raiz) is None


def _pagina(estados, siguiente=None):
    nodos = [{"isArchived": archivado, "fieldValueByName": {"name": e} if e else None} for e, archivado in estados]
    items = {"pageInfo": {"hasNextPage": siguiente is not None, "endCursor": siguiente}, "nodes": nodos}
    return json.dumps({"data": {"user": {"projectV2": {"items": items}}}})


def test_recuento_pagina_y_cuenta_por_estado(monkeypatch):
    paginas = {
        None: _pagina([("Backlog", False), ("Done", False), ("Done", True)], siguiente="c1"),
        "c1": _pagina([("In review", False), (None, False), ("Otro", False)]),
    }

    def run(args, **kwargs):
        assert args[:3] == ["gh", "api", "graphql"]
        cursor = next((a.removeprefix("cursor=") for a in args if a.startswith("cursor=")), None)
        return subprocess.CompletedProcess(args, 0, paginas[cursor], "")

    monkeypatch.setattr(github.subprocess, "run", run)
    assert github.recuento("davidbp845", 9) == {"Backlog": 1, "Ready": 0, "In progress": 0, "In review": 1, "Done": 1}


@pytest.mark.parametrize(
    "run",
    [
        lambda args, **kwargs: subprocess.CompletedProcess(args, 1, "", "gh: not logged in"),
        lambda args, **kwargs: subprocess.CompletedProcess(args, 0, '{"errors": [{"message": "x"}]}', ""),
    ],
)
def test_recuento_sin_gh_devuelve_none(monkeypatch, run):
    monkeypatch.setattr(github.subprocess, "run", run)
    assert github.recuento("davidbp845", 9) is None

import subprocess
from pathlib import Path

import pytest

import adrs
import github


def _git(carpeta: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(carpeta), *args], check=True, capture_output=True)


@pytest.mark.parametrize(
    ("texto", "estado"),
    [
        ("Aceptada.", "Aceptada"),
        ("Aceptada (2026-10-17, implementada y en uso).", "Aceptada"),
        ("Aceptada — implementada. Issue [#231](https://github.com/o/r/issues/231) cerrado", "Aceptada"),
        ("Superada por el [ADR-0006](0006-wagtail.md): Wagtail se activa.", "Superada"),
        ("Propuesta — issue #32.", "Propuesta"),
        ("rechazada: no compensa.", "Rechazada"),
        ("**Aceptada** (2026-10-23).", "Aceptada"),
        ("Vigente desde 2026.", None),
        ("", None),
    ],
)
def test_estado_es_la_primera_palabra(texto, estado):
    assert adrs.estado(texto) == estado


@pytest.mark.parametrize(
    ("texto", "issues"),
    [
        ("Implementación: issue #14.", [("o/r", 14)]),
        ("Implementación: #36 (alias), #37 (reglas) y #36 otra vez.", [("o/r", 36), ("o/r", 37)]),
        ("Implementación: [#1](https://github.com/o/home/issues/1).", [("o/home", 1)]),
        ("Ver https://github.com/o/otro/issues/9 y o/otro#10.", [("o/otro", 9), ("o/otro", 10)]),
        ("Superada por [ADR-0006](0006-x.md), sin issue.", []),
    ],
)
def test_issues_del_estado(texto, issues):
    assert adrs.issues(texto, "o/r") == issues


def test_sin_repo_un_numero_suelto_no_es_un_issue():
    assert adrs.issues("Propuesta — issue #3; ver o/r#4.", None) == [("o/r", 4)]


def _adr(carpeta: Path, nombre: str, texto: str) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_text(texto, encoding="utf-8")


def test_del_proyecto_lee_los_ficheros_y_no_el_indice(tmp_path):
    proyecto = tmp_path / "app"
    carpeta = proyecto / "doc" / "A2-ADR"
    _adr(carpeta, "README.md", "# A2\n\n| [0009](x) | Otra | Aceptada |\n")
    _adr(carpeta, "0001-csv.md", "# 0001 — CSV como almacenamiento\n\n## Estado\n\nAceptada — issue #3.\n")
    _adr(carpeta, "0002-sin-estado.md", "# 0002 — Sin estado\n\n## Contexto\n\nAceptada en Contexto no cuenta.\n")
    _git(proyecto, "init", "-q")
    _git(proyecto, "remote", "add", "origin", "git@github.com:o/app.git")

    leido = adrs.del_proyecto(proyecto)

    assert leido["repo"] == "o/app"
    assert leido["url_carpeta"] == "https://github.com/o/app/blob/HEAD/doc/A2-ADR"
    assert [(a["numero"], a["titulo"], a["estado"], a["issues"]) for a in leido["adrs"]] == [
        ("0001", "CSV como almacenamiento", "Aceptada", [("o/app", 3)]),
        ("0002", "Sin estado", None, []),
    ]


def test_del_proyecto_busca_en_el_primer_submodulo(tmp_path):
    contenedor = tmp_path / "contenedor"
    _adr(contenedor / "codigo" / "doc" / "A2-ADR", "0001-a.md", "# 0001 — A\n\n## Estado\n\nPropuesta.\n")
    (contenedor / ".gitmodules").write_text('[submodule "codigo"]\n\tpath = codigo\n\turl = x\n')
    leido = adrs.del_proyecto(contenedor)
    assert leido["repo"] is None
    assert leido["url_carpeta"] is None
    assert [a["estado"] for a in leido["adrs"]] == ["Propuesta"]


def test_sin_adr_no_hay_proyecto(tmp_path):
    _adr(tmp_path / "vacia" / "doc" / "A2-ADR", "README.md", "# A2\n")
    assert adrs.del_proyecto(tmp_path / "vacia") is None
    assert adrs.del_proyecto(tmp_path / "no-existe") is None


@pytest.mark.parametrize(
    ("estado", "abiertos", "implementacion", "revisar"),
    [
        ("Aceptada", [], None, False),
        ("Aceptada", [False, False], "hecha", False),
        ("Aceptada", [False, True], "en_curso", False),
        ("Aceptada", [False, None], None, False),
        ("Aceptada", [True, None], "en_curso", False),
        ("Propuesta", [False], "hecha", True),
        ("Propuesta", [True], "pendiente", False),
        ("Propuesta", [False, True], "pendiente", False),
        ("Propuesta", [None], None, False),
    ],
)
def test_implementacion_y_revision_salen_de_los_issues(estado, abiertos, implementacion, revisar):
    assert adrs.implementacion(estado, abiertos) == implementacion
    assert adrs.para_revisar(estado, abiertos) is revisar


@pytest.mark.parametrize(
    ("salida", "esperado"),
    [
        ('[{"number": 3, "state": "OPEN"}, {"number": 4, "state": "CLOSED"}]', {3: True, 4: False}),
        ("", None),
    ],
)
def test_issues_abiertos(monkeypatch, salida, esperado):
    monkeypatch.setattr(subprocess, "run", lambda args, **_kw: subprocess.CompletedProcess(args, 0, salida, ""))
    assert github.issues_abiertos("o/r") == esperado

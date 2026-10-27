import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import ram

FIXTURES = Path(__file__).parent / "fixtures"
APP = str(Path(__file__).parent.parent / "app.py")
LISTAR = "a\t4321\t8520\t8001\nb\t4322\t8521\t8002\n"


@pytest.fixture
def lanzadera(monkeypatch):
    """La app con el registro de fixtures y `dev_up.sh` simulado: nada arranca de verdad."""
    llamadas = []
    run_real, popen_real = subprocess.run, subprocess.Popen

    def run(cmd, *args, **kwargs):
        if cmd[:2] == ["./scripts/dev_up.sh", "--listar"]:
            return subprocess.CompletedProcess(cmd, 0, lanzadera.listar, "")
        if cmd == ["./scripts/dev_down.sh"]:
            llamadas.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return run_real(cmd, *args, **kwargs)

    def popen(cmd, *args, **kwargs):
        if cmd[0] == "./scripts/dev_up.sh":
            llamadas.append(cmd)
            return None
        return popen_real(cmd, *args, **kwargs)

    lanzadera.listar = LISTAR
    lanzadera.llamadas = llamadas
    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(FIXTURES))
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "Popen", popen)
    st.cache_data.clear()
    return lanzadera


def _abrir(buscar=""):
    at = AppTest.from_file(APP, default_timeout=30)
    # El buscador es un componente propio: AppTest no lo teclea, se le da su estado.
    at.session_state["buscar_proyecto"] = {"value": buscar}
    return at.run()


def _contador(at):
    # "N de M": los textos de las tarjetas de gráficos también pueden llevar " de ".
    return next(c.value for c in at.caption if re.fullmatch(r"\d+ de \d+", c.value))


def _nombres(at):
    return [m.value for m in at.markdown if m.value.startswith("**") and m.value not in {"**Proyecto**", "**Puerto**"}]


@pytest.mark.parametrize(
    ("buscar", "contador"),
    [("", "6 de 6"), ("multi", "1 de 6"), ("9502", "1 de 6"), ("negocio b", "1 de 6"), ("zzz", "0 de 6")],
)
def test_filtra_por_texto(lanzadera, buscar, contador):
    at = _abrir(buscar)
    assert not at.exception
    assert _contador(at) == contador


def test_negocios_multitenant_como_filas(lanzadera):
    at = _abrir()
    at.button_group(key="filtros_lanzadera").set_value(["Negocios"]).run()
    assert _contador(at) == "3 de 6"
    assert [n for n in _nombres(at) if "egocio" in n] == ["**Todos los negocios**", "**Negocio a**", "**Negocio b**"]


def test_sin_multitenant_la_fila_single(lanzadera):
    lanzadera.listar = ""
    at = _abrir()
    at.button_group(key="filtros_lanzadera").set_value(["Negocios"]).run()
    assert _contador(at) == "1 de 4"
    assert "**Único**" in _nombres(at)


def test_el_interruptor_de_un_negocio_relanza_el_stack(lanzadera, monkeypatch):
    at = _abrir()
    # Los puertos de los fixtures nunca se abren: sin esto, iniciar_negocios esperaría el máximo.
    # Solo aquí: AppTest también duerme mientras espera al script.
    monkeypatch.setattr(time, "sleep", lambda _segundos: None)
    at.toggle(key="switch_negocio_b").set_value(True).run()
    assert not at.exception
    assert lanzadera.llamadas == [
        ["./scripts/dev_down.sh"],
        ["./scripts/dev_up.sh", "--skip-checks", "--negocios", "b"],
    ]


def test_menu_sin_negocios(lanzadera):
    assert _abrir().sidebar.radio[0].options == ["Lanzadera", "Enlaces", "VPS", "Local"]


@pytest.fixture
def sin_negocios(lanzadera, monkeypatch, tmp_path):
    """El registro de fixtures sin `[negocios]`: un launcher sin heruka-flow."""
    registro = (FIXTURES / "proyectos.toml").read_text()
    (tmp_path / "proyectos.toml").write_text(registro[: registro.index("[negocios]")])
    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(tmp_path))
    return lanzadera


def test_sin_negocios_en_el_registro_no_hay_filas_ni_pildora(sin_negocios):
    at = _abrir()
    assert not at.exception
    assert _contador(at) == "3 de 3"
    assert "Negocios" not in at.button_group(key="filtros_lanzadera").options


def test_sin_negocios_local_mide_solo_los_proyectos(sin_negocios, monkeypatch):
    medidos = []

    def consultar(proyectos):
        medidos.extend(p["slug"] for p in proyectos)
        return {"medicion": {"proyectos": [], "compartidos": []}, "hora": datetime.now(), "error": None}

    monkeypatch.setattr(ram, "consultar", consultar)
    at = _abrir()
    at.sidebar.radio(key="pagina").set_value("Local").run()
    assert not at.exception
    assert medidos == ["esta", "simple", "multi"]

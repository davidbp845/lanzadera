import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import vps
from config.vps import cargar

FIXTURES = Path(__file__).parent / "fixtures"
SALIDA = "### Sistema\nhost     vps\n### Memoria\n       total\nMem:    3.8Gi\n### Servicios con fallo\n"


@pytest.mark.parametrize(
    ("salida", "esperado"),
    [
        (
            SALIDA,
            [("Sistema", "host     vps"), ("Memoria", "       total\nMem:    3.8Gi"), ("Servicios con fallo", "")],
        ),
        ("aviso previo\n### Disco\n/dev/sda1  38G\n", [("Disco", "/dev/sda1  38G")]),
        ("sin marcadores\n", []),
    ],
)
def test_trocea_por_secciones(salida, esperado):
    assert vps.trocear(salida) == esperado


@pytest.mark.parametrize(
    ("titulos", "esperado"),
    [
        (
            ["Sistema", "Memoria", "Servicios con fallo", "Disco", "Procesos con más RAM", "Contenedores"],
            [["Sistema", "Memoria", "Servicios con fallo"], ["Disco", "Procesos con más RAM"], ["Contenedores", None]],
        ),
        (["Disco", "Sistema"], [["Sistema", None, None], ["Disco", None]]),
        (["Sistema", "Nueva"], [["Sistema", None, None], ["Nueva"]]),
    ],
)
def test_reparte_por_titulo(titulos, esperado):
    filas = vps.repartir([(t, "") for t in titulos])
    assert [[s and s[0] for s in fila] for fila in filas] == esperado


def test_carga_los_servidores():
    assert cargar(FIXTURES / "vps.toml") == [{"nombre": "Pruebas", "host": "vps-pruebas"}]


def test_sin_fichero_no_hay_servidores(tmp_path):
    assert cargar(tmp_path / "vps.toml") == []


def _run_falso(returncode=0, stdout="", stderr="", excepcion=None):
    def run(cmd, **kwargs):
        if excepcion:
            raise excepcion
        assert cmd[:3] == ["ssh", "-o", "BatchMode=yes"] and cmd[-2:] == ["sh", "-s"]
        assert kwargs["input"].startswith("#!/bin/sh")
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

    return run


@pytest.mark.parametrize(
    ("run", "error", "secciones"),
    [
        (_run_falso(stdout=SALIDA), None, 3),
        (_run_falso(255, stderr="ssh: connect to host vps port 22: Connection timed out\n"), "Connection timed out", 0),
        (_run_falso(excepcion=subprocess.TimeoutExpired("ssh", 15)), "Sin respuesta de vps en 15 s", 0),
    ],
)
def test_consultar(monkeypatch, run, error, secciones):
    monkeypatch.setattr(vps.subprocess, "run", run)
    resultado = vps.consultar("vps")
    assert (resultado["error"] is None) if error is None else (error in resultado["error"])
    assert len(resultado["secciones"]) == secciones


def test_pagina_vps_consulta_al_entrar_y_al_refrescar(monkeypatch):
    llamadas = []

    def consultar(host):
        llamadas.append(host)
        return {"secciones": vps.trocear(SALIDA), "hora": datetime.now(), "duracion": 1.4, "error": None}

    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(FIXTURES))
    monkeypatch.setattr(vps, "consultar", consultar)
    at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("VPS").run()
    assert not at.exception
    assert [c.value for c in at.code] == ["host     vps", "       total\nMem:    3.8Gi", "(sin salida)"]
    at.run()
    assert llamadas == ["vps-pruebas"]
    at.button[0].click().run()
    assert llamadas == ["vps-pruebas", "vps-pruebas"]

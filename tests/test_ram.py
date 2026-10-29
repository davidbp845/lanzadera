from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import ram
from config.proyectos import cargar

FIXTURES = Path(__file__).parent / "fixtures"
RAIZ = Path("/data")

# Esta app (9501) arrancó Simple desde el panel; Multi se lanzó a mano: su UI cuelga
# de un wrapper (pnpm) y la API se ha reparentado fuera de up.sh. Otro proyecto
# comparte ./start.sh con Simple en otra carpeta.
PS = """\
  100     1  50000 streamlit run app.py
  200   100   1000 bash ./start.sh
  201   200  80000 streamlit run simple.py
  300     1   2000 bash ./up.sh
  301   300  10000 pnpm dev
  302   301 300000 node next-server
  310     1 400000 python api.py
  400     1   9999 bash ./start.sh
"""
CWD = {200: "/data/Apps/simple", 300: "/data/Otros/multi", 400: "/data/Apps/otro"}
PUERTOS = {9501: 100, 9502: 201, 9503: 310, 9504: 302}


@pytest.fixture
def proyectos():
    return cargar(FIXTURES / "proyectos.toml", RAIZ)["proyectos"]


def _medir(proyectos, puertos=PUERTOS):
    return ram.medir(proyectos, ram.parsear_ps(PS), puertos, CWD.get)


def _por_nombre(medicion):
    return {m["nombre"]: m for m in medicion["proyectos"]}


def test_parsea_ps_con_argumentos_y_sin_ellos():
    assert ram.parsear_ps("  7  1  300 bash ./up.sh --skip\n  8  7  0\n\n") == {
        7: (1, 300, "bash ./up.sh --skip"),
        8: (7, 0, ""),
    }


def test_ram_por_proyecto_de_mayor_a_menor(proyectos):
    medicion = _medir(proyectos)
    assert [(m["nombre"], m["kb"]) for m in medicion["proyectos"]] == [
        ("Multi", 2000 + 10000 + 300000 + 400000),
        ("Simple", 1000 + 80000),
        ("Esta app", 50000),
    ]
    assert medicion["compartidos"] == []


def test_esta_app_no_suma_los_proyectos_que_arranco(proyectos):
    assert _por_nombre(_medir(proyectos))["Esta app"]["pids"] == {100}


def test_parsea_ss_con_puertos_de_otro_usuario():
    salida = (
        'LISTEN 0 128 127.0.0.1:8501 0.0.0.0:* users:(("streamlit",pid=100,fd=6))\n'
        "LISTEN 0 4096 0.0.0.0:8510 0.0.0.0:*\n"
        'LISTEN 0 511 [::]:8510 [::]:* users:(("docker-proxy",pid=7,fd=4))\n'
        "LISTEN 0 4096 [::]:8510 [::]:*\n"
    )
    assert ram.parsear_ss(salida) == {8501: 100, 8510: 7}
    assert ram.parsear_ss("LISTEN 0 4096 *:8511 *:*\n") == {8511: None}


# Además de las raíces de verdad (bash -> bash relanzado, dos instancias), procesos de
# la misma carpeta que solo nombran el script o el programa.
RAICES = """  500     1  0 bash ./start.sh
  501   500  0 bash ./start.sh
  510     1  0 bash ./start.sh
  520     1  0 vim start.sh
  530     1  0 npm install
  540     1  0 node /usr/bin/npm run dev -- --port 8508
"""


@pytest.mark.parametrize(
    ("cmd", "esperado"),
    [(["./start.sh"], {500, 510}), (["npm", "run", "dev", "--", "--port", "8508"], {540})],
)
def test_raices_reales_por_comando_y_carpeta(cmd, esperado):
    filas = ram.parsear_ps(RAICES)
    assert ram.raices_reales(cmd, RAIZ / "Apps/x", filas, lambda pid: "/data/Apps/x") == esperado


def test_desglose_por_servicio_con_el_script_aparte(proyectos):
    # El wrapper pnpm queda por encima del proceso del puerto: cuenta con el script.
    # El admin comparte puerto con la UI: es el mismo servicio y no sale aparte.
    assert _por_nombre(_medir(proyectos))["Multi"]["desglose"] == [
        ("UI", 9504, 300000),
        ("API", 9503, 400000),
        (ram.SCRIPT_ARRANQUE, None, 2000 + 10000),
    ]


def test_solo_cuenta_los_activos(proyectos):
    puertos = {k: v for k, v in PUERTOS.items() if k != 9502}
    assert "Simple" not in _por_nombre(_medir(proyectos, puertos))


def test_activo_de_otro_usuario_sin_ram(proyectos):
    medicion = _medir(proyectos, {**PUERTOS, 9502: None})
    assert [(m["nombre"], m["kb"]) for m in medicion["proyectos"]][-1] == ("Simple", None)


def test_avisa_de_procesos_compartidos(proyectos):
    # La API de Multi resulta ser el streamlit de Simple: se contaría dos veces.
    assert _medir(proyectos, {**PUERTOS, 9503: 201})["compartidos"] == [("Simple", "Multi")]


@pytest.mark.parametrize(
    ("kb", "texto"),
    [(144384, "141 MB"), (1000 * 1024, "1000 MB"), (1024 * 1024, "1,00 GB"), (2202010, "2,10 GB"), (0, "0 MB")],
)
def test_formatear(kb, texto):
    assert ram.formatear(kb) == texto


def test_pagina_local_mide_al_entrar_y_al_recalcular(monkeypatch, proyectos):
    llamadas = []

    def consultar(proyectos_registro):
        llamadas.append(len(proyectos_registro))
        return {"medicion": _medir(proyectos), "hora": datetime.now(), "error": None}

    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(FIXTURES))
    monkeypatch.setattr(ram, "consultar", consultar)
    at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Local").run()
    assert not at.exception
    tabla = at.dataframe[0].value
    assert list(tabla["Proyecto"]) == ["Multi", "Simple", "Esta app", "Total"]
    assert tabla["RAM"].iloc[-1] == ram.formatear(712000 + 81000 + 50000)
    assert len(at.expander) == 1
    at.run()
    # Los tres [[proyecto]] del fixture más [negocios.single].
    assert llamadas == [4]
    at.button[0].click().run()
    assert llamadas == [4, 4]

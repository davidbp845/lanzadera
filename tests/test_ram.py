from collections import namedtuple
from datetime import datetime
from pathlib import Path

import psutil
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


def _filas(texto: str) -> ram.Filas:
    """Procesos escritos como `pid ppid rss_kb línea de comando`, una línea por proceso."""
    filas = {}
    for linea in texto.splitlines():
        partes = linea.split(None, 3)
        if len(partes) >= 3:
            filas[int(partes[0])] = (int(partes[1]), int(partes[2]), partes[3] if len(partes) == 4 else "")
    return filas


@pytest.fixture
def proyectos():
    return cargar(FIXTURES / "proyectos.toml", RAIZ)["proyectos"]


def _medir(proyectos, puertos=PUERTOS):
    return ram.medir(proyectos, _filas(PS), puertos, CWD.get)


def _por_nombre(medicion):
    return {m["nombre"]: m for m in medicion["proyectos"]}


class _Proceso:
    def __init__(self, pid, info):
        self.pid, self.info = pid, info


def test_lee_procesos_con_y_sin_acceso(monkeypatch):
    memoria = namedtuple("memoria", "rss")
    procesos = [
        _Proceso(7, {"ppid": 1, "memory_info": memoria(300 * 1024), "cmdline": ["bash", "./up.sh", "--skip"]}),
        # De otro usuario o de sistema: psutil da None en lo que no puede leer.
        _Proceso(8, {"ppid": None, "memory_info": None, "cmdline": None}),
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda _atributos: iter(procesos))
    assert ram.leer_procesos() == {7: (1, 300, "bash ./up.sh --skip"), 8: (0, 0, "")}


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


Conexion = namedtuple("Conexion", "laddr status pid")
Direccion = namedtuple("Direccion", "ip port")


def test_puertos_en_escucha_con_puertos_de_otro_usuario():
    conexiones = [
        Conexion(Direccion("127.0.0.1", 8501), psutil.CONN_LISTEN, 100),
        Conexion(Direccion("0.0.0.0", 8510), psutil.CONN_LISTEN, None),
        Conexion(Direccion("::", 8510), psutil.CONN_LISTEN, 7),
        Conexion(Direccion("::", 8510), psutil.CONN_LISTEN, None),
        Conexion(Direccion("127.0.0.1", 40000), psutil.CONN_ESTABLISHED, 100),
    ]
    assert ram.puertos_de(conexiones) == {8501: 100, 8510: 7}
    assert ram.puertos_de([Conexion(Direccion("::", 8511), psutil.CONN_LISTEN, None)]) == {8511: None}


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
    filas = _filas(RAICES)
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


# Stack de negocios: dev_up.sh con el backend común de hijo, que escucha las APIs de todos
# los negocios; el frontend estático se ha reparentado fuera del script. El negocio b está parado.
PS_NEGOCIOS = """\
  600     1   3000 bash ./scripts/dev_up.sh --skip-checks --negocios a
  601   600 500000 python main.py
  602   600  60000 streamlit run panel.py
  610     1  20000 python -m http.server 4321
"""
NEGOCIOS = ram.fila_heruka_flow(
    [{"id": "a", "front": 4321, "panel": 8520, "api": 8001}, {"id": "b", "front": 4322, "panel": 8521, "api": 8002}],
    RAIZ / "Otros/negocios",
    {"nombre": "Único"},
)


def _medir_negocios(puertos):
    return ram.medir([NEGOCIOS], _filas(PS_NEGOCIOS), puertos, {600: "/data/Otros/negocios"}.get)


def test_negocios_sin_puerto_principal_con_el_backend_en_una_linea():
    (medido,) = _medir_negocios({4321: 610, 8520: 602, 8000: 601, 8001: 601, 8002: 601})["proyectos"]
    assert medido["kb"] == 3000 + 500000 + 60000 + 20000
    assert medido["desglose"] == [
        ("Negocio a · Frontend", 4321, 20000),
        ("Negocio a · Panel", 8520, 60000),
        ("Negocio b · Frontend", 4322, 0),
        ("Negocio b · Panel", 8521, 0),
        ("Backend común", 8001, 500000),
        (ram.SCRIPT_ARRANQUE, None, 3000),
    ]


@pytest.mark.parametrize(("puertos", "kb"), [({}, "inactivo"), ({4322: None}, None)])
def test_negocios_activos_por_cualquier_servicio(puertos, kb):
    medidos = _medir_negocios(puertos)["proyectos"]
    assert [m["kb"] for m in medidos] == ([] if kb == "inactivo" else [kb])


def test_sin_negocios_la_fila_es_el_single():
    assert ram.fila_heruka_flow([], RAIZ / "Otros/negocios", {"nombre": "Único"}) == {"nombre": "Único"}


# Proyecto sin puerto (ADR-0017): un script de AutoHotkey lanzado con un .cmd que se queda de padre.
PS_PROCESO = """\
  700     1   1000 cmd.exe /c start.cmd
  701   700  30000 C:\\AutoHotkey\\AutoHotkey64.exe atajos.ahk
  702   701   5000 C:\\AutoHotkey\\AutoHotkey64.exe atajos.ahk /child
  710     1   2000 notepad.exe otro.ahk
"""
SIN_PUERTO = {"nombre": "Atajos", "puerto": None, "proceso": "atajos.ahk"}


def test_raices_de_proceso_toma_el_de_mas_arriba():
    assert ram.raices_de_proceso("atajos.ahk", _filas(PS_PROCESO)) == {701}
    assert ram.raices_de_proceso("no-existe.ahk", _filas(PS_PROCESO)) == set()


def test_mide_un_proyecto_sin_puerto_por_proceso():
    (medido,) = ram.medir([SIN_PUERTO], _filas(PS_PROCESO), {})["proyectos"]
    assert (medido["puerto"], medido["pids"], medido["kb"]) == (None, {701, 702}, 35000)
    assert ram.medir([{**SIN_PUERTO, "proceso": "parado.ahk"}], _filas(PS_PROCESO), {})["proyectos"] == []


def test_raices_reales_con_rutas_de_windows():
    filas = _filas(PS_PROCESO)
    cmd = ["AutoHotkey64.exe", "atajos.ahk"]
    assert ram.raices_reales(cmd, RAIZ / "Windows/atajos", filas, lambda pid: "/data/Windows/atajos") == {701}


class _Arbol:
    """Proceso simulado de psutil: registra lo que se le hace."""

    def __init__(self, pid, hijos=(), sigue_vivo=False):
        self.pid, self.hijos, self.sigue_vivo, self.hecho = pid, list(hijos), sigue_vivo, []

    def children(self, recursive):
        return self.hijos

    def terminate(self):
        self.hecho.append("terminate")

    def kill(self):
        self.hecho.append("kill")


def test_terminar_en_windows_para_el_arbol_y_mata_lo_que_queda(monkeypatch):
    hijo = _Arbol(702, sigue_vivo=True)
    raiz = _Arbol(701, [hijo])

    def wait_procs(procesos, timeout):
        return [p for p in procesos if not p.sigue_vivo], [p for p in procesos if p.sigue_vivo]

    monkeypatch.setattr(psutil, "Process", lambda pid: raiz)
    monkeypatch.setattr(psutil, "wait_procs", wait_procs)
    ram.terminar(701, windows=True)
    assert (raiz.hecho, hijo.hecho) == (["terminate"], ["terminate", "kill"])


def test_terminar_en_linux_manda_sigterm_al_grupo(monkeypatch):
    enviados = []
    # raising=False: en Windows `os` no tiene getpgid ni killpg.
    monkeypatch.setattr(ram.os, "getpgid", lambda pid: pid * 10, raising=False)
    monkeypatch.setattr(ram.os, "killpg", lambda grupo, senal: enviados.append((grupo, senal)), raising=False)
    ram.terminar(701, windows=False)
    assert enviados == [(7010, ram.signal.SIGTERM)]


def test_memoria_total_de_la_maquina(monkeypatch):
    monkeypatch.setattr(psutil, "virtual_memory", lambda: namedtuple("memoria", "total")(16303932 * 1024))
    assert ram.memoria_total_kb() == 16303932

    def falla():
        raise OSError

    monkeypatch.setattr(psutil, "virtual_memory", falla)
    assert ram.memoria_total_kb() is None

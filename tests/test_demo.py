import socket
import subprocess
from datetime import date
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import actividad
import demo
import graficos
import ram
import textos
import vps
from config import paths

APP = str(Path(__file__).parent.parent / "app.py")
PAGINAS = ["Lanzadera", "Enlaces", "VPS", "Local"]


@pytest.fixture
def modo_demo(monkeypatch):
    """La app en modo demo; cualquier proceso o socket que se abra hace fallar el test."""

    def prohibido(*_args, **_kwargs):
        raise AssertionError("en la demo no se ejecuta nada del sistema")

    monkeypatch.setenv("HOME_LAUNCHER_DEMO", "1")
    monkeypatch.delenv("HOME_LAUNCHER_DATOS", raising=False)
    monkeypatch.delenv("HOME_LAUNCHER_IDIOMA", raising=False)
    for nombre in ["run", "Popen", "check_output", "check_call", "call"]:
        monkeypatch.setattr(subprocess, nombre, prohibido)
    monkeypatch.setattr(socket, "socket", prohibido)
    st.cache_data.clear()


def _abrir(pagina="Lanzadera"):
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["buscar_proyecto"] = {"value": ""}
    at.run()
    if pagina != "Lanzadera":
        at.sidebar.radio(key="pagina").set_value(pagina).run()
    return at


@pytest.mark.parametrize("idioma", ["en", "es"])
@pytest.mark.parametrize("pagina", PAGINAS)
def test_las_paginas_de_la_demo_no_ejecutan_nada(modo_demo, monkeypatch, pagina, idioma):
    # Por entorno y no por session_state: AppTest aplica el format_func del menú fuera de la
    # ejecución del script, donde solo ve el idioma por defecto.
    monkeypatch.setenv("HOME_LAUNCHER_IDIOMA", idioma)
    at = _abrir(pagina)
    assert not at.exception
    assert at.info[0].value == textos.texto(idioma, "demo.aviso")


def test_la_demo_empieza_en_ingles_con_los_interruptores_deshabilitados(modo_demo):
    at = _abrir()
    assert at.title[0].value == "Launchpad"
    assert at.sidebar.radio(key="pagina").options == ["Launchpad", "Links", "VPS", "Local"]
    assert at.toggle and all(toggle.disabled for toggle in at.toggle)


def test_los_graficos_siguen_plegados_al_volver_de_otra_pagina(modo_demo):
    at = _abrir()
    assert len(at.get("vega_lite_chart")) == 2
    # Un botón en cada tarjeta: cualquiera de los dos pliega las dos.
    at.button(key="plegar_actividad").click().run()
    assert not at.get("vega_lite_chart")
    at.sidebar.radio(key="pagina").set_value("VPS").run()
    at.sidebar.radio(key="pagina").set_value("Lanzadera").run()
    assert not at.get("vega_lite_chart")
    at.button(key="plegar_issues").click().run()
    assert len(at.get("vega_lite_chart")) == 2


def test_los_dos_idiomas_tienen_los_mismos_textos():
    assert textos.TEXTOS["es"].keys() == textos.TEXTOS["en"].keys()


@pytest.mark.parametrize(
    ("entorno", "demo_activa", "idioma"),
    [
        ({}, False, "es"),
        ({"HOME_LAUNCHER_DEMO": "1"}, True, "en"),
        ({"HOME_LAUNCHER_DEMO": "1", "HOME_LAUNCHER_IDIOMA": "es"}, True, "es"),
        ({"HOME_LAUNCHER_IDIOMA": "en"}, False, "en"),
        ({"HOME_LAUNCHER_IDIOMA": "fr"}, False, "es"),
    ],
)
def test_modo_demo_e_idioma_por_entorno(monkeypatch, entorno, demo_activa, idioma):
    monkeypatch.delenv("HOME_LAUNCHER_DEMO", raising=False)
    monkeypatch.delenv("HOME_LAUNCHER_IDIOMA", raising=False)
    monkeypatch.delenv("HOME_LAUNCHER_DATOS", raising=False)
    for clave, valor in entorno.items():
        monkeypatch.setenv(clave, valor)
    assert paths.demo() is demo_activa
    assert paths.idioma() == idioma
    assert (paths.datos() == paths.DEMO) is demo_activa


def test_la_ram_de_la_demo_solo_cuenta_los_activos():
    proyectos = [{"nombre": "A", "slug": "notes", "puerto": 8510}, {"nombre": "B", "slug": "contacts", "puerto": 8530}]
    medidos = demo.ram(proyectos)["medicion"]["proyectos"]
    assert [(m["nombre"], m["kb"], len(m["desglose"])) for m in medidos] == [("A", 310 * 1024, 2)]


# Salida real de estado_vps.sh y la de la demo, que usa "load" en vez de "carga".
SISTEMA = "host     vps\n{carga}    0.18  0.22  0.19   (2 CPU)"
MEMORIA = (
    "       total    used    free  available\nMem:   3.8Gi   1.6Gi   412Mi      2.2Gi\nSwap:  1.0Gi    96Mi   928Mi"
)
DISCO = "Filesystem  Size  Used Avail Use% Mounted on\n/dev/sda1    38G   21G   16G  58% /\n/dev/sda15  124M   12M  113M  10% /boot/efi"


@pytest.mark.parametrize("carga", ["carga", "load"])
def test_medidores_del_vps(carga):
    secciones = [
        ("Sistema", SISTEMA.format(carga=carga)),
        ("Memoria", MEMORIA),
        ("Disco", DISCO),
        ("Servicios con fallo", "0 servicios con fallo"),
    ]
    medidas = vps.medidores(secciones)
    usado, total, disponible = medidas["memoria"]
    assert round(usado / total * 100) == 42 and disponible == 2.2 * 2**30
    assert medidas["disco"] == (58, "21G", "38G")
    assert medidas["carga"] == (0.18, 2)
    assert medidas["fallos"] == 0


@pytest.mark.parametrize(
    ("fallos", "esperado"),
    [("0 servicios con fallo", 0), ("a.service loaded failed failed A\nb.service loaded failed failed B", 2)],
)
def test_medidores_cuentan_los_servicios_con_fallo(fallos, esperado):
    assert vps.medidores([("Servicios con fallo", fallos)])["fallos"] == esperado


def test_medidores_sin_secciones_no_fallan():
    assert vps.medidores([("Sistema", "host vps")]) == {"memoria": None, "disco": None, "carga": None, "fallos": None}


def test_commits_por_dia_suma_los_repositorios_y_rellena_con_ceros(monkeypatch):
    salidas = {"a": "2026-10-20\n2026-10-20\n2026-10-22\n", "b": "2026-10-22\n"}
    monkeypatch.setattr(actividad, "_git", lambda *args: salidas[Path(args[1]).name])
    commits = actividad.commits_por_dia({Path("a"), Path("b")}, date(2026, 10, 19), date(2026, 10, 22))
    assert list(commits.values()) == [0, 2, 0, 2]


def test_memoria_total_de_la_maquina(tmp_path):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal:       16303932 kB\nMemFree:         1234 kB\n")
    assert ram.memoria_total_kb(meminfo) == 16303932
    assert ram.memoria_total_kb(tmp_path / "no-existe") is None


@pytest.mark.parametrize(
    ("valores", "esperado"),
    [
        ([], [1, 2, 3, 4, 5]),
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 3, 5, 7, 9]),
        ([0, 20, 20, 20], [1, 20, 21, 22, 23]),
    ],
)
def test_cortes_del_mapa_de_actividad_segun_los_datos(valores, esperado):
    assert graficos.cortes(valores) == esperado


@pytest.mark.parametrize(
    ("nombres", "maximo", "esperado"),
    [
        (["Home"], 36, "Home"),
        (["Acme Studio (acme)", "Notes vault", "Budget tracker"], 36, "acme · Notes vault · Budget tracker"),
        (["Acme Studio (acme)", "Notes vault", "Budget tracker"], 24, "acme · Notes vault +1"),
        (["Acme Studio (acme)", "Notes vault", "Budget tracker"], 8, "acme +2"),
        (["Un nombre muy largo sin alias"], 12, "Un nombre m…"),
        (["Un nombre muy largo sin alias", "Otro"], 12, "Un nombr… +1"),
    ],
)
def test_etiqueta_de_un_tablero_compartido_se_resume_si_no_cabe(nombres, maximo, esperado):
    assert graficos.etiqueta_tablero(nombres, maximo) == esperado


def test_actualizar_tableros_refresca_tambien_el_grafico(modo_demo, monkeypatch):
    llamadas = []

    def recuento(owner, numero):
        llamadas.append(numero)
        # Un issue más en Backlog en cada consulta: se ve si el gráfico usa la nueva.
        return {"Backlog": len(llamadas), "Ready": 0, "In progress": 0, "In review": 0, "Done": 0}

    monkeypatch.setattr(demo, "recuento", recuento)
    at = _abrir()
    at.button(key="plegar_issues").click().run()
    antes = next(c.value for c in at.caption if "open issues" in c.value)
    at.button(key="actualizar_tableros").click().run()
    despues = next(c.value for c in at.caption if "open issues" in c.value)
    assert antes != despues


def test_un_fallo_de_gh_no_se_queda_en_cache(modo_demo, monkeypatch):
    red = {"hay": False}

    def recuento(owner, numero):
        return {"Backlog": 1, "Ready": 0, "In progress": 0, "In review": 0, "Done": 0} if red["hay"] else None

    monkeypatch.setattr(demo, "recuento", recuento)
    vacio = textos.TEXTOS["en"]["issues.vacio"]
    at = _abrir()
    assert any(vacio in c.value for c in at.caption)
    red["hay"] = True
    at.run()
    assert not any(vacio in c.value for c in at.caption)


def test_parpadea_solo_la_pastilla_in_progress_del_tablero_con_una_sesion_trabajando(modo_demo):
    at = _abrir()
    latidos = [m.value for m in at.markdown if 'class="latido"' in m.value]
    assert len(latidos) == 1
    assert 'title="In progress · Claude Code working now on: #3 ' in latidos[0]

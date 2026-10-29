from pathlib import Path

import pytest

from config import paths
from config.proyectos import cargar, url_enlace

FIXTURE = Path(__file__).parent / "fixtures" / "proyectos.toml"
RAIZ = Path("/data")


@pytest.fixture
def registro():
    return cargar(FIXTURE, RAIZ)


def test_mantiene_el_orden_del_fichero(registro):
    assert [p["slug"] for p in registro["proyectos"]] == ["esta", "simple", "multi"]


def test_resuelve_las_rutas_contra_la_raiz_data(registro):
    assert registro["proyectos"][1]["path"] == RAIZ / "Apps/simple"
    assert registro["heruka_flow"] == RAIZ / "Otros/negocios"


def test_sin_cmd_es_esta_app(registro):
    assert registro["proyectos"][0]["cmd"] is None


@pytest.mark.parametrize(
    ("indice", "esperado"),
    [
        (1, None),
        (
            2,
            [
                ("UI", 9504, "", "localhost"),
                ("API", 9503, "/health", "localhost"),
                ("Admin", 9504, "/admin/", "admin.localhost"),
            ],
        ),
    ],
)
def test_enlaces_como_tuplas(registro, indice, esperado):
    assert registro["proyectos"][indice].get("enlaces") == esperado


def test_url_de_cada_enlace(registro):
    assert [url_enlace(e) for e in registro["proyectos"][2]["enlaces"]] == [
        "http://localhost:9504",
        "http://localhost:9503/health",
        "http://admin.localhost:9504/admin/",
    ]


def test_conserva_las_claves_opcionales(registro):
    multi = registro["proyectos"][2]
    assert multi["cmd_detener"] == ["./down.sh"]
    assert multi["intentos_espera_inicio"] == 60
    assert registro["proyectos"][1]["env"] == {"VARIABLE": "valor"}


def test_negocios(registro):
    assert registro["intentos_negocios"] == 100
    assert registro["heruka_life_single"]["path"] == RAIZ / "Otros/negocios"


def test_sin_negocios(tmp_path):
    fichero = tmp_path / "proyectos.toml"
    texto = FIXTURE.read_text()
    fichero.write_text(texto[: texto.index("[negocios]")])
    registro = cargar(fichero, RAIZ)
    assert registro["heruka_flow"] is None
    assert registro["heruka_life_single"] is None


def test_rutas_por_defecto_y_por_entorno(monkeypatch, tmp_path):
    monkeypatch.delenv("HOME_LAUNCHER_DATOS", raising=False)
    monkeypatch.delenv("HOME_LAUNCHER_RAIZ", raising=False)
    assert paths.datos() == paths.RAIZ_REPO.parent / "datos"
    assert paths.raiz_data() == paths.RAIZ_REPO.parents[2]
    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(tmp_path))
    assert paths.enlaces() == tmp_path / "enlaces.csv"


def test_el_registro_real_carga():
    # Lee ../datos solo para validar su formato; no comprueba su contenido.
    if not paths.proyectos().exists():
        pytest.skip("sin contenedor de datos")
    registro = cargar()
    assert registro["proyectos"]

import pytest

from config.prioridades import cambiar, cargar, guardar


def test_ignora_lo_que_no_es_una_prioridad_de_1_a_5(tmp_path):
    ruta = tmp_path / "prioridades.toml"
    ruta.write_text('a = 3\nb = 0\nc = 6\nd = true\ne = "4"\n', encoding="utf-8")
    assert cargar(ruta) == {"a": 3}


def test_sin_fichero_no_hay_prioridades(tmp_path):
    assert cargar(tmp_path / "prioridades.toml") == {}


def test_guardar_y_cargar_dan_lo_mismo(tmp_path):
    ruta = tmp_path / "prioridades.toml"
    guardar(ruta, {"negocio-a": 2, "multi": 5})
    assert cargar(ruta) == {"multi": 5, "negocio-a": 2}


@pytest.mark.parametrize(
    ("actual", "paso", "esperado"),
    [(3, 1, 4), (3, -1, 2), (5, 1, 5), (1, -1, 1), (None, 1, 1), (None, -1, None)],
)
def test_cambiar_sube_o_baja_una_unidad_dentro_de_1_a_5(actual, paso, esperado):
    inicial = {} if actual is None else {"x": actual}
    assert cambiar(inicial, "x", paso).get("x") == esperado

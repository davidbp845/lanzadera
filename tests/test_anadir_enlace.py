import csv
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.anadir_enlace import EnlaceRechazado, anadir

SCRIPT = Path(__file__).parent.parent / "scripts" / "anadir_enlace.py"


@pytest.fixture
def datos(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(tmp_path))
    return tmp_path


def filas(ruta: Path) -> list[list[str]]:
    with ruta.open(newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_crea_la_cabecera_si_falta(datos):
    anadir("Docs", "https://docs.example.com", "Documentación")
    assert filas(datos / "enlaces.csv") == [
        ["descripcion", "enlace", "etiquetas"],
        ["Docs", "https://docs.example.com", "Documentación"],
    ]


@pytest.mark.parametrize("final", ["\n", ""])
def test_anade_la_fila_al_final(datos, final):
    (datos / "enlaces.csv").write_text("descripcion,enlace,etiquetas\nA,https://a.example.com,X" + final)
    anadir("B", "https://b.example.com", "Y;Revisar")
    assert filas(datos / "enlaces.csv")[1:] == [
        ["A", "https://a.example.com", "X"],
        ["B", "https://b.example.com", "Y;Revisar"],
    ]


def test_escapa_comas_y_comillas(datos):
    anadir('Sitio "raro", con coma', "https://x.example.com", "A;B")
    assert filas(datos / "enlaces.csv")[1] == ['Sitio "raro", con coma', "https://x.example.com", "A;B"]


@pytest.mark.parametrize("url", ["docs.example.com", "ftp://x.example.com", ""])
def test_rechaza_una_url_sin_esquema_http(datos, url):
    with pytest.raises(EnlaceRechazado):
        anadir("Docs", url, "")
    assert not (datos / "enlaces.csv").exists()


@pytest.mark.parametrize(
    "repetida",
    [
        "https://docs.example.com/guia",
        "https://docs.example.com/guia/",
        "http://docs.example.com/guia",
        "https://www.docs.example.com/guia",
        "https://Docs.Example.com/guia",
    ],
)
def test_no_duplica_una_url_existente(datos, repetida):
    anadir("Docs", "https://docs.example.com/guia", "")
    antes = (datos / "enlaces.csv").read_text()
    with pytest.raises(EnlaceRechazado, match="https://docs.example.com/guia"):
        anadir("Otra descripción", repetida, "")
    assert (datos / "enlaces.csv").read_text() == antes


def test_distingue_rutas_que_solo_comparten_prefijo(datos):
    anadir("Docs", "https://docs.example.com/guia", "")
    anadir("Docs API", "https://docs.example.com/guia/api", "")
    assert len(filas(datos / "enlaces.csv")) == 3


@pytest.mark.parametrize(
    ("args", "codigo"),
    [(["Docs", "https://docs.example.com", "X"], 0), (["Docs", "docs.example.com", "X"], 1), (["Docs"], 2)],
)
def test_codigo_de_salida(datos, args, codigo):
    resultado = subprocess.run([sys.executable, SCRIPT, *args], check=False, capture_output=True, text=True)
    assert resultado.returncode == codigo

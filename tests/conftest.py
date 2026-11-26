import pytest


@pytest.fixture(autouse=True)
def datos_temporales(monkeypatch, tmp_path):
    """Ningún test lee ni escribe en los datos reales: los que necesitan datos los fijan aparte."""
    monkeypatch.setenv("HOME_LAUNCHER_DATOS", str(tmp_path))


def ir_a(at, url_path: str):
    """Abre en `at` el apartado del menú con ese `url_path` (`""`, el de por defecto) y lo ejecuta.

    `AppTest.switch_page` solo encuentra páginas de fichero, y las del panel son funciones
    de `app.py`: se busca su hash entre las que registró `st.navigation` en la última ejecución.
    """
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url_path)
    return at.run()

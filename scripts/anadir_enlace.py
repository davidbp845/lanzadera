"""Añade un enlace a `enlaces.csv` para que aparezca en la página Enlaces.

Uso: `python3 scripts/anadir_enlace.py "descripcion" "url" "etiqueta1;etiqueta2"`

Es el punto de entrada para quien no sea el panel (`/crear-enlace`, automatizaciones de
otras apps): así no necesitan conocer la ruta ni el formato del CSV. No hace commit; el
cambio queda en el contenedor para revisarlo. Sale con código distinto de cero si no escribe la fila.
"""

import csv
import sys
from pathlib import Path

# Ejecutado como script, sys.path[0] es scripts/: la raíz del repo hace falta para `config`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import paths

CABECERA = ["descripcion", "enlace", "etiquetas"]


class EnlaceRechazado(Exception):
    pass


def anadir(descripcion: str, url: str, etiquetas: str, ruta: Path | None = None) -> Path:
    """Escribe la fila y devuelve la ruta del CSV; `EnlaceRechazado` si la URL no vale o ya está."""
    ruta = ruta or paths.enlaces()
    if not url.startswith(("http://", "https://")):
        raise EnlaceRechazado(f"la URL debe empezar por http:// o https://: {url}")
    existe = ruta.exists()
    if existe:
        texto = ruta.read_text(encoding="utf-8")
        if any(fila.get("enlace") == url for fila in csv.DictReader(texto.splitlines())):
            raise EnlaceRechazado(f"la URL ya está en {ruta}: {url}")
    with ruta.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not existe:
            w.writerow(CABECERA)
        elif texto and not texto.endswith("\n"):
            # Sin esto, la fila nueva se pegaría a la última del fichero.
            f.write("\n")
        w.writerow([descripcion, url, etiquetas])
    return ruta


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    try:
        ruta = anadir(*argv)
    except EnlaceRechazado as e:
        print(f"No se añade: {e}", file=sys.stderr)
        return 1
    print(f"Añadido a {ruta}: {argv[0]} · {argv[1]} · {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

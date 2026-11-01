"""ADR de cada proyecto, leídas de su `doc/A2-ADR/` sin escribir nada (ADR-0020).

La fuente es cada fichero `NNNN-*.md`, no el índice: el título es su primera línea y el
estado, la primera palabra de `## Estado`; los issues relacionados, los que cita esa sección.
"""

import re
import subprocess
from pathlib import Path

import github

ESTADOS = ["Propuesta", "Aceptada", "Superada", "Rechazada"]
CARPETA = Path("doc") / "A2-ADR"

FICHERO = re.compile(r"^(\d{4})-.+\.md$")
TITULO = re.compile(r"^#\s+(?:\d{4}\s*[—–-]\s*)?(.+?)\s*$")
SECCION_ESTADO = re.compile(r"^##\s+Estado\s*$(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
# `[#1](https://github.com/o/r/issues/1)`: el texto del enlace no dice el repo, la URL sí.
ENLACE_ISSUE = re.compile(r"\[[^\]]*\]\(https?://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)[^)]*\)")
URL_ISSUE = re.compile(r"https?://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)")
REF_ISSUE = re.compile(r"(?<![\w/#])(?:([\w.-]+/[\w.-]+))?#(\d+)\b")


def estado(texto: str) -> str | None:
    """El estado canónico de la sección `## Estado`; None si su primera palabra no es uno de `ESTADOS`."""
    palabra = re.match(r"\W*(\w+)", texto)
    if not palabra:
        return None
    return next((e for e in ESTADOS if e.lower() == palabra.group(1).lower()), None)


def issues(texto: str, repo: str | None) -> list[tuple[str, int]]:
    """`(owner/repo, número)` de los issues que cita el texto, en orden y sin repetir.

    Un `#NN` suelto es del repo del proyecto; sin repo conocido, se descarta.
    """
    encontrados = [(r, int(n)) for r, n in ENLACE_ISSUE.findall(texto)]
    texto = ENLACE_ISSUE.sub(" ", texto)
    encontrados += [(r, int(n)) for r, n in URL_ISSUE.findall(texto)]
    texto = URL_ISSUE.sub(" ", texto)
    encontrados += [(r or repo, int(n)) for r, n in REF_ISSUE.findall(texto) if r or repo]
    return list(dict.fromkeys(encontrados))


def leer_adr(fichero: Path, repo: str | None) -> dict:
    texto = fichero.read_text(encoding="utf-8", errors="ignore")
    primera = texto.lstrip().splitlines()[0] if texto.strip() else ""
    titulo = m.group(1) if (m := TITULO.match(primera)) else fichero.stem
    seccion = m.group(1).strip() if (m := SECCION_ESTADO.search(texto)) else ""
    return {
        "numero": FICHERO.match(fichero.name).group(1),
        "titulo": titulo,
        "fichero": fichero.name,
        "estado": estado(seccion),
        "issues": issues(seccion, repo),
    }


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, encoding="utf-8", timeout=2, check=False
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def carpeta(path: Path) -> Path | None:
    """`doc/A2-ADR/` del proyecto o, si no la tiene (contenedor solo local), la de su primer submódulo."""
    if (path / CARPETA).is_dir():
        return path / CARPETA
    if (path / ".gitmodules").is_file():
        submodulos = _git("config", "-f", str(path / ".gitmodules"), "--get-regexp", r"^submodule\..*\.path$")
        if submodulos and (path / submodulos.splitlines()[0].split()[-1] / CARPETA).is_dir():
            return path / submodulos.splitlines()[0].split()[-1] / CARPETA
    return None


def slug(url: str | None) -> str | None:
    """`https://github.com/o/r` -> `o/r`; None si no es de GitHub."""
    m = re.fullmatch(r"https://github\.com/([\w.-]+/[\w.-]+)", url or "")
    return m.group(1) if m else None


def del_proyecto(path: Path) -> dict | None:
    """`{"carpeta", "repo", "url_carpeta", "adrs"}` del proyecto; None si no tiene `doc/A2-ADR/` con ADR.

    `repo` es `owner/repo` y `url_carpeta`, la carpeta en GitHub; los dos None sin remoto de GitHub.
    """
    directorio = carpeta(path)
    if not directorio:
        return None
    ficheros = sorted(f for f in directorio.iterdir() if f.is_file() and FICHERO.match(f.name))
    if not ficheros:
        return None
    url = github.repositorio(directorio)
    repo = slug(url)
    prefijo = _git("-C", str(directorio), "rev-parse", "--show-prefix").rstrip("/")
    return {
        "carpeta": str(directorio.resolve()),
        "repo": repo,
        "url_carpeta": f"{url}/blob/HEAD/{prefijo}" if repo and prefijo else None,
        "adrs": [leer_adr(f, repo) for f in ficheros],
    }


def implementacion(abiertos: list[bool | None]) -> str | None:
    """`hecha` si todos sus issues están cerrados, `en_curso` si alguno sigue abierto; None sin issues
    o si no se sabe el estado de alguno."""
    if not abiertos or (None in abiertos and True not in abiertos):
        return None
    return "en_curso" if True in abiertos else "hecha"


def para_revisar(adr_estado: str | None, abiertos: list[bool | None]) -> bool:
    """Una Propuesta con todos sus issues cerrados: o se aceptó y falta escribirlo, o sobra el issue."""
    return adr_estado == "Propuesta" and implementacion(abiertos) == "hecha"

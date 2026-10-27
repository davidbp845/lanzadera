"""Enlaces a GitHub de cada proyecto (repositorio y tablero), deducidos de su carpeta, y recuento del tablero.

Los enlaces salen sin red; el recuento consulta la API de GitHub con el `gh` del usuario.
"""

import json
import re
import subprocess
from pathlib import Path

# La línea que fija el tablero en la sección `## Método` del método común.
TABLERO = re.compile(r"^- Tablero:.*owner `([^`]+)`, número `(\d+)`", re.MULTILINE)


def url_web(remoto: str) -> str | None:
    """`git@github.com:o/r.git` o `https://github.com/o/r.git` -> `https://github.com/o/r`."""
    remoto = remoto.strip().removesuffix(".git")
    if coincidencia := re.fullmatch(r"(?:ssh://)?git@([^:/]+)[:/](.+)", remoto):
        return f"https://{coincidencia.group(1)}/{coincidencia.group(2)}"
    if remoto.startswith(("https://", "http://")):
        return remoto
    return None


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=2, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def repositorio(path: Path) -> str | None:
    """El `origin` de la carpeta o, si no tiene (contenedor solo local), el de su primer submódulo."""
    if not path.is_dir():
        return None
    remoto = _git("-C", str(path), "remote", "get-url", "origin")
    if not remoto and (path / ".gitmodules").is_file():
        submodulos = _git("config", "-f", str(path / ".gitmodules"), "--get-regexp", r"^submodule\..*\.url$")
        remoto = submodulos.splitlines()[0].split()[-1] if submodulos else ""
    return url_web(remoto) if remoto else None


def tablero_id(path: Path, raiz: Path) -> tuple[str, int] | None:
    """`(owner, número)` del `CLAUDE.md` con `## Método` más cercano subiendo desde `path`, sin pasar de `raiz`."""
    for carpeta in [path, *path.parents]:
        if not carpeta.is_relative_to(raiz):
            break
        fichero = carpeta / "CLAUDE.md"
        if fichero.is_file():
            texto = fichero.read_text(errors="ignore")
            if "## Método" in texto:
                coincidencia = TABLERO.search(texto)
                return (coincidencia.group(1), int(coincidencia.group(2))) if coincidencia else None
    return None


def tablero(path: Path, raiz: Path) -> str | None:
    identificador = tablero_id(path, raiz)
    return f"https://github.com/users/{identificador[0]}/projects/{identificador[1]}" if identificador else None


ESTADOS = ["Backlog", "Ready", "In progress", "In review", "Done"]

CONSULTA = """
query($owner: String!, $numero: Int!, $cursor: String) {
  user(login: $owner) {
    projectV2(number: $numero) {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isArchived
          fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
        }
      }
    }
  }
}
"""


def contar(nodos: list[dict]) -> dict[str, int]:
    """Items no archivados por Status, con todos los de `ESTADOS` aunque estén a cero."""
    cuenta = dict.fromkeys(ESTADOS, 0)
    for nodo in nodos:
        estado = (nodo.get("fieldValueByName") or {}).get("name")
        if not nodo.get("isArchived") and estado in cuenta:
            cuenta[estado] += 1
    return cuenta


def recuento(owner: str, numero: int) -> dict[str, int] | None:
    """Recuento por estado de un tablero de GitHub Projects; None si `gh` falla (sin red, sin sesión...)."""
    nodos: list[dict] = []
    cursor = None
    while True:
        args = ["gh", "api", "graphql", "-f", f"query={CONSULTA}", "-f", f"owner={owner}", "-F", f"numero={numero}"]
        if cursor:
            args += ["-f", f"cursor={cursor}"]
        try:
            resultado = subprocess.run(args, capture_output=True, text=True, timeout=10, check=False)
            items = json.loads(resultado.stdout)["data"]["user"]["projectV2"]["items"]
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
            return None
        nodos += items["nodes"]
        if not items["pageInfo"]["hasNextPage"]:
            return contar(nodos)
        cursor = items["pageInfo"]["endCursor"]

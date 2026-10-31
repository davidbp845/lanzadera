"""Negocios multi-tenant de heruka-flow: sus puertos los decide `dev_up.sh --listar` (ADR-0005)."""

import subprocess
from pathlib import Path


def parsear_listar(salida: str) -> list[dict]:
    """Una línea `id<TAB>frontend<TAB>panel<TAB>api` por negocio."""
    negocios = []
    for linea in salida.splitlines():
        partes = linea.split("\t")
        if len(partes) == 4:
            negocio_id, front, panel, api = partes
            negocios.append({"id": negocio_id, "front": int(front), "panel": int(panel), "api": int(api)})
    return negocios


def listar(ruta: Path) -> list[dict]:
    """Los negocios de heruka-flow en `ruta`; vacío si no hay multi-tenant o el script no responde."""
    try:
        salida = subprocess.run(
            ["./scripts/dev_up.sh", "--listar"],
            cwd=ruta,
            check=False,
            capture_output=True,
            encoding="utf-8",
            timeout=10,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return parsear_listar(salida)

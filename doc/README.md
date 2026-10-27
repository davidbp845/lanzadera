# Documentación de home

> **Borrador (2026-10-23)**: primera versión, escrita al aplicar la metodología de los proyectos hermanos. Hay que revisarla entera.

Ver [metodología](A0-Metodologia/metodologia-de-diseno-y-desarrollo.md), donde se explican los tres niveles de trabajo (A, B y C).

Las rutas de código que aparecen en estos documentos (`app.py`, `config/`, `tests/`...) son relativas a la raíz de este repo. `datos/` está fuera de él, en el repo contenedor solo local (`../datos`) ([ADR-0001](A2-ADR/0001-contenedor-local-con-los-datos.md)).

Esta documentación es la fuente de verdad sobre el proceso y la metodología. Si algo de aquí contradice a la memoria de Claude Code o a un `CLAUDE.md`, prevalece este documento: hay que actualizar o borrar el fragmento afectado.

## Nivel A — Visión y arquitectura

- [A0 — Metodología](A0-Metodologia/metodologia-de-diseno-y-desarrollo.md)
- [A1 — Visión](A1-Vision/README.md)
	- Problema, entradas y salidas, modelo de datos
	- Casos de uso y comandos de Claude Code
	- Páginas del panel (Lanzadera con los negocios, Enlaces, VPS, Local)
	- Integraciones con los proyectos hermanos, systemd y la terminal
- [A2 — ADR](A2-ADR/README.md)
	- Contenedor local con los datos; código y doc, submódulo
	- Arranque y parada delegados en cada proyecto
	- El puerto como fuente de verdad del estado
	- Registro de proyectos como dato
	- Negocios: los puertos los decide heruka-flow
	- El launcher como servicio de systemd
	- Estructura plana, sin hexagonal
	- Página VPS: estado por SSH bajo demanda
	- Negocios como filas de la Lanzadera

## Nivel B — Alta de proyecto en el launcher

- [B1 — Fichas de proyecto](B1-Fichas-proyecto/README.md)
- [B2 — Diseños técnicos](B2-Disenos-tecnicos/README.md)
- [B3 — Puesta en marcha](B3-Puesta-marcha/README.md)

## Nivel C — Ciclo de feature/issue

Issues y su estado: [tablero (proyecto GitHub #9)](https://github.com/users/davidbp845/projects/9).

- [C1 — Análisis](C1-Analisis/README.md)
- [C2 — Diseño técnico](C2-Diseno-tecnico/README.md)
- [C3 — Diseño UX/UI](C3-Diseno-UX-UI/README.md)
- [C4 — Implementación](C4-Implementacion/README.md)
- [C5 — Verificación](C5-Verificacion/README.md)
- [C6 — Revisión](C6-Revision/README.md)
- [C7 — Cierre](C7-Cierre/README.md)

## Otros

- [Z-Anexos](Z-Anexos/README.md)
	- Patrón multi-servicio
	- Lecciones aprendidas

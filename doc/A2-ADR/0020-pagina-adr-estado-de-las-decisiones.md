# 0020 — Página ADR: el estado de las decisiones, leído de `doc/A2-ADR/` de cada proyecto

## Contexto

Los proyectos que siguen el método común guardan sus decisiones de arquitectura en `doc/A2-ADR/`, un fichero por decisión con una sección `## Estado`, más un índice en `README.md`. Desde la Lanzadera se ve el estado de los tableros, pero no el de esas decisiones: cuántas siguen en Propuesta, cuáles ya están implementadas, cuál se ha quedado con un estado que no cuadra con sus issues.

Los índices tienen formatos distintos según el proyecto (tabla, lista con estado, lista sin él). El Estado de cada fichero es texto libre, pero en todos empieza por la palabra del estado (`Aceptada`, `Propuesta`, `Superada por…`), y los issues relacionados salen en esa misma sección como `#NN` o como enlace a GitHub. «Aceptada» mezcla decisiones implementadas y pendientes, y nada la pone al día cuando se cierra su issue.

## Decisión

- **Página ADR**, la segunda del menú, tras Lanzadera: un gráfico de ADR por proyecto y estado, una tarjeta «Para revisar», un desplegable de proyecto y la tabla de sus ADR (número, decisión, estado, implementación e issues).
- **La fuente es el fichero de cada ADR, no el índice**: `doc/A2-ADR/NNNN-*.md` de la carpeta del registro o, si no la tiene, de su primer submódulo (como el remoto de GitHub). Solo lectura. Las filas que comparten carpeta cuentan una vez, con sus nombres juntos, como los tableros.
- **Contrato del Estado** (lo que se lee, `adrs.py`):
  - Título: la primera línea, `# NNNN — Decisión`.
  - Estado: la primera palabra de `## Estado`, uno de `Propuesta` · `Aceptada` · `Superada` · `Rechazada`. Otra palabra, o sin sección, sale como «sin clasificar» y no rompe la página.
  - Issues: los de `## Estado`, como `#NN` (del repo del proyecto), `owner/repo#NN` o enlace `https://github.com/owner/repo/issues/NN`.
- **El estado es solo el de la decisión; la implementación se deduce de sus issues** en GitHub: hecha si todos están cerrados, en curso si alguno sigue abierto, «—» sin issues. Una consulta `gh issue list --state all` por repo, en paralelo, cacheada 10 minutos; sin `gh`, los issues salen sin estado.
- **«Para revisar»** señala la incoherencia que se puede detectar: una ADR en Propuesta con todos sus issues cerrados.
- **El método común mantiene el contrato**: `/dev:crear-decision` escribe el Estado con él, y `/dev:cerrar-issue` propone pasar a Aceptada la ADR en Propuesta cuyo último issue cierra.

## Alternativas descartadas

- **Leer el índice `README.md`**: tiene tres formatos y puede desfasarse del fichero; habría que normalizar los de cada proyecto.
- **Un estado `Implementada` escrito a mano**: obliga a reescribir las ADR de todos los proyectos y a mantenerlo al cerrar cada issue; el estado de los issues ya lo dice GitHub.
- **Un fichero de estado aparte (TOML o JSON) por proyecto**: duplica lo que dice la ADR y se desincroniza igual.

## Consecuencias

- Las ADR que hay ya se leen sin tocar los otros repos.
- Una ADR que no siga el contrato se ve como «sin clasificar», y así se detecta.
- El launcher lee la documentación de los proyectos hermanos y, con `gh`, sus issues: un contrato más con ellos ([6 — Integraciones](../A1-Vision/6-integraciones.md)).
- La demo enseña ADR de ejemplo desde `demo/estado.toml`.

## Estado

Aceptada (2026-11-01) — issue [#11](https://github.com/davidbp845/lanzadera/issues/11).

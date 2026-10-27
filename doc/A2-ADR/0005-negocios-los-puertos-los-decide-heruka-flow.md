# 0005 — Negocios: los puertos los decide heruka-flow

## Contexto

heruka-flow pasó a multi-tenant: varios negocios, cada uno con frontend, panel y API, sobre un único backend (`:8000`). La lista de negocios y sus puertos cambia en heruka-flow, no en home.

## Decisión

- La página Negocios pide la lista a `scripts/dev_up.sh --listar` en cada carga; home no repite puertos de negocios.
- Franjas reservadas para no pisar el resto: frontends 4321-4329, paneles 8520-8529, APIs 8001-8009.
- Cambiar la selección (arrancar o parar uno) para el stack entero con `dev_down.sh` y lo vuelve a levantar con `dev_up.sh --negocios` y los elegidos, porque el backend es compartido.
- Si `--listar` no devuelve nada, se muestra la fila única `[negocios.single]` (Heruka Life single-tenant).
- Página propia, separada de Proyectos (desde 2026-10-21).

## Alternativas descartadas

- **Un `[[proyecto]]` por negocio**: duplicaría en home la configuración de heruka-flow y no reflejaría el backend compartido.

## Consecuencias

- Parar un negocio reinicia los demás (~36 s de arranque del backend).
- Depende del formato de salida de `--listar` (cuatro columnas separadas por tabulador).

## Estado

Aceptada (multi-tenant desde 2026-09-19). El punto "Página propia, separada de Proyectos" queda superado por [ADR-0009](0009-negocios-como-filas-de-la-lanzadera.md).

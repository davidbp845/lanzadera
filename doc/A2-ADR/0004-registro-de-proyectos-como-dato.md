# 0004 — Registro de proyectos como dato (`datos/proyectos.toml`)

## Contexto

La lista `PROYECTOS` era una constante de `app.py`, con comentarios largos que explicaban cada caso. Dar de alta un proyecto era un commit de código ("Launcher: añade X"), aunque no cambiara ninguna lógica.

## Decisión

- El registro vive en `datos/proyectos.toml`: `[[proyecto]]` por fila, y `[negocios]`/`[negocios.single]` para la página Negocios ([3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md)).
- Las rutas son relativas a `Data`, no absolutas, para que el registro no dependa del punto de montaje.
- Los comentarios que explican el porqué de las claves de una fila viajan con la fila, en el TOML.
- `config/proyectos.py:cargar()` lo convierte en los dicts que ya usaba `app.py` (con `path` absoluto y `enlaces` como tuplas), sin cambiar `iniciar()`/`detener()`.
- Se relee en cada rerun: un alta se ve al refrescar el panel.

## Alternativas descartadas

- **YAML**: necesita dependencia; `tomllib` viene con Python.
- **JSON**: sin comentarios, que aquí son esenciales.
- **CSV como `enlaces.csv`**: no admite listas ni tablas (`cmd`, `env`, `enlaces`).

## Consecuencias

- Dar de alta un proyecto estándar es un commit en el contenedor, no en el submódulo.
- Una clave nueva del registro sí es código (y probablemente un ADR).
- El registro ejecuta comandos: es tan sensible como un script.

## Estado

Aceptada (2026-10-23).

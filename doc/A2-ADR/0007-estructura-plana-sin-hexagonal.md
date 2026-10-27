# 0007 — Estructura plana (`app.py` + `config/`), sin hexagonal

## Contexto

Los proyectos hermanos usan una arquitectura hexagonal ligera (`domain/`, `application/`, `adapters/`). home no tiene dominio propio: es un panel que lee dos ficheros, comprueba puertos y lanza comandos.

## Decisión

- `app.py`: páginas Streamlit y control de procesos (puertos, arranque, parada, negocios).
- `config/paths.py`: rutas a `datos/` y a `Data`.
- `config/proyectos.py`: carga del registro.
- `tests/`: cargador y rutas, con fixtures ficticios. Las páginas se comprueban con `streamlit.testing.v1.AppTest` en la verificación (C5).
- Reglas mínimas: rutas a datos solo vía `config/paths.py`; ningún comando de arranque concreto en el código ([ADR-0002](0002-arranque-y-parada-delegados-en-cada-proyecto.md)).

## Alternativas descartadas

- **Hexagonal completa**: puertos y adaptadores para un único caso de uso (arrancar/parar) añadirían más estructura que código.

## Consecuencias

- Si `app.py` crece (RAM en el panel, logs, validación del registro), el primer paso es sacar el control de procesos a un módulo `procesos.py` con tests propios.

## Estado

Aceptada (2026-10-23), a revisar si el launcher crece.

# 0002 — Arranque y parada delegados en el script o servicio de cada proyecto

## Contexto

Al principio el registro tenía comandos completos (`venv/bin/python -m streamlit run streamlit_app/app.py`). Cuando `conocimiento` movió su código a un submódulo y empezó a exportar variables de entorno al arrancar, el comando de home dejó de funcionar. Heruka Life levanta tres procesos y deja algunos (`astro dev`) fuera del grupo de procesos, así que matar por puerto no los para todos.

## Decisión

- `cmd` llama al script del propio proyecto (`./start.sh`, `scripts/dev_up.sh`) o a su servicio (`systemctl --user start X`), nunca a un comando reconstruido en home. Excepción aceptada: los Astro sin backend, con `npm run dev -- --port N`.
- Si matar a quien escucha el puerto no basta (varios procesos, Docker, systemd), el proyecto aporta su `cmd_detener` y home lo usa.
- Si un proyecto solo tiene instrucciones en prosa (un comando de Claude), primero se crea el script en ese proyecto y después la fila en home.
- Todo arranque debe ser no interactivo: se lanza con `Popen`, salida a `/dev/null` y `start_new_session=True`.

## Alternativas descartadas

- **Reconstruir el comando en home**: se rompe en cuanto el proyecto cambia su estructura o su entorno.
- **Lógica de parada específica en `app.py`**: duplica lo que el proyecto ya sabe y se desfasa.

## Consecuencias

- home es estable frente a reestructuraciones internas de los proyectos: solo cambia su `ruta`.
- Diagnosticar un arranque fallido requiere ir al proyecto (home no guarda su salida).

## Estado

Aceptada (2026-08-22, con Heruka Life; reforzada el 2026-09-03 con conocimiento).

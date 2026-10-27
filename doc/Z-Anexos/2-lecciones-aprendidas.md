# 3. Lecciones aprendidas

## Un proyecto se reestructura y el interruptor deja de funcionar (2026-09-03)

Un proyecto movió su código a un submódulo y su `start.sh` empezó a exportar una variable de entorno. home tenía el comando completo con las rutas viejas y falló sin dar error (salida a `/dev/null`). Origen del [ADR-0002](../A2-ADR/0002-arranque-y-parada-delegados-en-cada-proyecto.md): usar el script del proyecto.

## Verde antes de tiempo en proyectos multi-servicio (2026-09-14)

Se supuso que el panel de Heruka Life era el último en arrancar; medido en los logs, era el primero (frontend ~12 s, backend ~36 s). Ahora `iniciar()` espera a todos los puertos de `enlaces` ([ADR-0003](../A2-ADR/0003-el-puerto-como-fuente-de-verdad.md)). Moraleja: medir en los logs, no suponer.

## Heruka Consola vuelve a "parado" sola (2026-09-10)

Con el margen por defecto (10 s) el backend aún no respondía y el semáforo volvía a ⚪. Se añadió `intentos_espera_inicio`.

## El filtro de Enlaces deja de funcionar al volver a la página (2026-09-12)

`st.html(..., unsafe_allow_javascript=True)` inserta el JS en el documento principal, que persiste al navegar. Al volver, se redeclaraba una `const` global, saltaba un `SyntaxError` y los botones dejaban de responder hasta recargar. Solución: el JS en una IIFE.

## Puerto de Docker sin PID visible (2026-10-15)

En un proyecto con Docker Compose, quien escucha es `docker-proxy` (root) y `ss -p` no da su PID al usuario: el `detener()` por defecto no paraba nada. Solución: `cmd_detener` con `docker compose down`.

## La Lanzadera se estrecha al escribir en el buscador (2026-10-27)

La vista se pedía dos veces: `centered` al principio de `app.py` y `wide` al final, en la rama de la página. El buscador lanza un rerun tras cada pausa al escribir y el siguiente interrumpe al anterior: si lo cortaba entre las dos llamadas, la página se quedaba estrecha. Solución: una sola `st.set_page_config` al principio, con la página que ya está en `st.session_state["pagina"]`.

## La cebra de la Lanzadera no cuadra con las filas (2026-10-27)

Streamlit da a cada `stMarkdownContainer` un `margin-bottom: -1rem` que compensa el margen del párrafo. En una celda de HTML propio (sin `<p>`) el bloque cuenta 16 px menos de lo que mide, el centrado vertical lo baja y el contenido se sale del fondo de la fila. Además, el hueco entre contenedores hermanos hace que las filas sin fondo parezcan más altas. Solución: `margin-bottom: 0` (y `p { margin: 0 }`) dentro de las filas y `gap: 0` en el contenedor que las agrupa. Para ver estas cosas sin navegador a mano: Chromium sin ventana por el protocolo de DevTools, esperando a que Streamlit pinte antes de capturar.

## AppTest no encuentra la página al cambiar de idioma (2026-10-27)

`AppTest` aplica el `format_func` del menú al leer el estado de los widgets, fuera de la ejecución del script: ahí `st.session_state` está vacío y el texto sale en el idioma por defecto. Con el idioma puesto en `session_state` y un nombre de página que cambia entre idiomas ("Enlaces" / "Links"), `set_value` fallaba con `x not in list`. Solución en los tests: fijar el idioma con `HOME_LAUNCHER_IDIOMA`, no en `session_state`.

## Capturar una página concreta del panel (2026-10-27)

El menú no va en la URL, así que Chromium sin ventana solo captura la Lanzadera. Para las demás: un script envoltorio, fuera del repo, que pone `st.session_state["pagina"]` desde `?p=` y ejecuta `app.py` con `runpy`; `--virtual-time-budget` da tiempo a que Streamlit pinte. El Chromium de snap solo escribe en `~/snap/chromium/common/`.

## El servicio sigue con la versión vieja de un módulo (2026-10-27)

Streamlit vuelve a ejecutar `app.py` en cada rerun, pero los módulos que importa (`graficos.py`, `vps.py`…) se quedan en memoria con la versión con la que arrancó el servicio; ni tocar el fichero los recarga. Si `app.py` ya usa la versión nueva, la página falla (p. ej. `TypeError` por un argumento con otra forma). Solución: tras cambiar un módulo importado, reiniciar `home-streamlit` (avisando antes: para lo arrancado desde el launcher). Un cambio solo en `app.py` no lo necesita.

# 0016 — Latido del issue en curso en un campo del tablero

## Contexto

La pastilla *In progress* de cada proyecto cuenta items del tablero, pero no dice si ahora mismo hay una sesión de Claude Code trabajando en uno de ellos. Un issue puede quedarse días en *In progress* sin que nadie lo toque, y desde el panel no se distingue de uno que se está resolviendo en este momento.

Las sesiones pueden correr en este equipo o en el VPS, sin conexión entre ambos; lo único que comparten es GitHub. El launcher ya lee cada tablero con una consulta GraphQL de solo lectura, cacheada 10 minutos ([5 — Panel](../A1-Vision/5-panel-streamlit.md)), y no se refresca solo: vigilar en continuo está [fuera de alcance](../A1-Vision/7-fuera-de-alcance.md).

## Decisión

- **La señal la da el plugin `dev` del método común**, no el launcher: `/dev:resolver-issue` y `/dev:sprint` fijan el issue en curso al pasarlo a *In progress* y `/dev:cerrar-issue` lo quita; unos hooks de la sesión mantienen la marca mientras tanto. Detalle en el README del plugin.
- **La marca es la hora UTC (ISO 8601) en un campo de texto `Latido` del tablero.** Los hooks la reescriben como mucho cada 5 minutos mientras la sesión trabaja y la vacían al acabar cada turno.
- **El launcher la lee en la misma consulta del recuento**: `github.recuento()` devuelve, además de los items por estado, `en_curso`, los issues *In progress* no archivados con un latido de hace menos de 15 minutos. Un tablero sin el campo devuelve `null` y no parpadea nunca.
- **La pastilla *In progress* parpadea** (animación CSS de opacidad) si `en_curso` no está vacío, con esos issues en su tooltip. Con `prefers-reduced-motion`, sin animación y con un contorno.
- **Se acepta el retraso de la caché**: el parpadeo puede tardar hasta 10 minutos en salir o en irse, o salir al momento con **Actualizar tableros**. Sin refresco periódico.

## Alternativas descartadas

- **Etiqueta en el issue**: no lleva hora, así que una sesión muerta la dejaría puesta para siempre, y cada alta y baja queda en el historial del issue.
- **Comentario en el issue**: ensucia el hilo y es más caro de leer en la consulta del tablero.
- **Número del issue sacado de la rama `NN-...`**: los proyectos trabajan en `main`, sin ramas por issue; sin rama no habría señal.
- **Refresco periódico solo de las pastillas** (`st.fragment(run_every=...)`): daría la señal al minuto, pero es vigilancia continua, fuera de alcance, y multiplica las consultas a GitHub.

## Consecuencias

- Desde la Lanzadera se distingue un *In progress* vivo de uno parado, también de sesiones en el VPS.
- Cada tablero que quiera la señal necesita el campo `Latido` creado a mano una vez, y el `gh` de cada máquina, el alcance `project`.
- Si la sesión muere sin avisar, el campo se queda con la última hora; deja de contar a los 15 minutos y lo vacía el siguiente `Stop` de una sesión sobre ese issue.
- El campo es visible en el tablero de GitHub (se puede ocultar de la vista).
- La forma del recuento cambia: `recuento()` y `demo.recuento()` devuelven también `en_curso`. La demo enseña el parpadeo con un ejemplo en `demo/estado.toml`.

## Estado

Aceptada (2026-10-30) — issue [#3](https://github.com/davidbp845/lanzadera/issues/3).

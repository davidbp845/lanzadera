# 0013 — Host opcional en los enlaces de un proyecto

## Contexto

Cada enlace de una fila se construye como `http://localhost:<puerto><ruta_url>` (`app.py`, `_pintar_enlaces`). Hay proyectos que sirven cosas distintas según el host de la petición, en el mismo puerto. Por ejemplo, una app Django multisite con su admin solo en `admin.localhost`: un enlace al admin que vaya a `localhost:<puerto>/admin/` da 404. La única forma de enlazarlo hoy es una fila en `datos/enlaces.csv`, fuera de la fila del proyecto.

Una clave nueva del registro es código y lleva ADR ([0004](0004-registro-de-proyectos-como-dato.md)).

## Decisión

- Cada entrada de `enlaces` admite una clave opcional `host`, por defecto `localhost`: `{etiqueta, puerto, ruta_url?, host?}`. El enlace pasa a ser `http://<host>:<puerto><ruta_url>`.
- `host` solo cambia la URL que abre el navegador. El estado sigue saliendo del puerto en `127.0.0.1` ([0003](0003-el-puerto-como-fuente-de-verdad.md)), y la espera de `iniciar()` y el recuento de RAM tratan una sola vez un puerto que se repite en varios enlaces.
- Se admite cualquier nombre que resuelva a la máquina local. Los subdominios de `localhost` (`admin.localhost`) los resuelven los navegadores sin tocar `/etc/hosts`.

## Alternativas descartadas

- **Una clave `url` completa por enlace**: el puerto dejaría de ser un campo propio, y `iniciar()` y el semáforo tendrían que sacarlo de la URL.
- **Admitir una URL absoluta en `ruta_url`**: mezcla dos significados en una clave, y cada caso tendría que distinguir si empieza por `/` o por `http`.
- **Dejarlo en `datos/enlaces.csv`**: funciona sin código, pero el enlace queda lejos de la fila del proyecto y no se enciende ni se apaga con ella.

## Consecuencias

- Una fila puede tener dos enlaces en el mismo puerto (la app y su admin). Hay que comprobar que la espera y la RAM no lo cuentan dos veces.
- El panel no comprueba que el enlace responda. Si el proyecto solo activa ese host con una variable local, el enlace se ve igual y da 404 mientras esté apagado, como ya pasa con cualquier `ruta_url`.
- La demo pinta estos enlaces como el resto de enlaces a localhost: sin destino ([0010](0010-demo-publica-de-solo-lectura.md)).
- Hay que actualizar `doc/A1-Vision/3-modelo-de-datos.md` (tabla de `enlaces` y forma de las tuplas) y los tests de `config/proyectos.py`.

## Estado

Propuesta (2026-10-29) — issue [#6](https://github.com/davidbp845/lanzadera/issues/6).

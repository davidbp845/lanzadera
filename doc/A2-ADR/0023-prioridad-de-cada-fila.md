# 0023 — Prioridad de cada fila en `datos/prioridades.toml`, escrita desde el panel

## Contexto

La tabla de la Lanzadera se ordena por el orden del registro, por las cabeceras (nombre, puerto, estado, enlaces) o por issues de un estado del tablero. Ninguno de esos órdenes dice qué proyectos importan más ahora, y ese orden cambia a menudo: tiene que poder ajustarse desde la propia tabla, sin editar un fichero.

Hasta ahora el panel solo lee `datos/`. Una prioridad que dure entre sesiones obliga a escribir allí. Meterla como clave de `datos/proyectos.toml` es código y lleva ADR ([0004](0004-registro-de-proyectos-como-dato.md)), y reescribir ese TOML desde el panel sin perder sus comentarios, que son parte del dato, pediría una dependencia nueva. Además, las filas de negocios multi-tenant no son `[[proyecto]]` del registro.

## Decisión

- **Fichero aparte `prioridades.toml`** en la carpeta de datos (`config/paths.py`, `HOME_LAUNCHER_DATOS` o `../datos`): una línea `slug = número` por fila. Lo escribe solo el panel; el registro no cambia. Cuentan todas las filas de la Lanzadera, también los negocios, por su slug. Un slug que ya no está en el registro se ignora.
- **Escala de 1 a 5**, 5 lo más prioritario. Una fila sin entrada no tiene prioridad («—»).
- **Columna Prioridad** entre Proyecto / Aplicación y Puerto, con cabecera ordenable como las demás, salvo que el primer clic ordena de más a menos prioridad (el segundo, al revés; el tercero, vuelta al orden del registro). «—» va al final en los dos sentidos; a igualdad, el orden del registro. Se excluye con las píldoras de orden por issues, como el resto de cabeceras.
- **Flechas ↑/↓ en cada fila**, solo con la tabla ordenada por prioridad: suben o bajan una unidad y escriben el fichero en ese mismo rerun. ↑ se deshabilita en 5 y ↓ en 1; en una fila sin prioridad, ↑ la pone en 1 y ↓ está deshabilitada.
- **Demo** ([ADR-0010](0010-demo-publica-de-solo-lectura.md)): parte de `demo/prioridades.toml`, con valores de ejemplo; las flechas cambian la prioridad solo en `st.session_state` y nunca escriben en disco.

## Alternativas descartadas

- **Clave `prioridad` en `datos/proyectos.toml`**: el panel tendría que reescribir el registro, que ejecuta comandos y cuyos comentarios hay que conservar (`tomlkit`, dependencia nueva), y los negocios multi-tenant no tendrían dónde guardarla.
- **Solo en la sesión**: sin escribir nada, pero el orden se pierde al recargar o al reiniciar `home-streamlit`.
- **Escala amplia (0–100) o posiciones sin tope**: con flechas de una unidad, mover una fila de un extremo a otro serían decenas de clics; y la escala P0–P4, con el número más bajo como lo más urgente, choca con el orden descendente.

## Consecuencias

- El panel deja de ser de solo lectura sobre `datos/`: cada clic en una flecha deja `prioridades.toml` modificado en el contenedor, sin commit, como hace `scripts/anadir_enlace.py` con `enlaces.csv`.
- Cada carpeta de datos tiene sus prioridades: `datos-windows/` ([ADR-0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md)) lleva su propio fichero.
- Cinco niveles para unas veinte filas dejan muchos empates, que se resuelven por el orden del registro.
- La tabla gana una columna: `COLUMNAS_LANZADERA` pasa a siete anchos.
- Los tests escriben en una carpeta temporal de `HOME_LAUNCHER_DATOS` y comprueban que en la demo no se escribe nada.
- Docs a actualizar al implementar: [3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md) (fichero nuevo) y [5 — Panel](../A1-Vision/5-panel-streamlit.md) (columna, orden y flechas).

## Estado

Propuesta (2026-11-26) — issue [#22](https://github.com/davidbp845/lanzadera/issues/22).

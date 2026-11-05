# 0022 — Tipo opcional en cada enlace y filtro por tipo a nivel de enlace

## Contexto

Las píldoras de tipo de la Lanzadera filtran por el `tipo` de cada fila, un solo valor: el framework del servicio del puerto principal ([ADR-0015](0015-tipo-de-aplicacion-en-el-registro.md)). Las filas de negocios son `heruka-flow`, fijado en código.

Los proyectos con varios servicios no encajan: Heruka Life (`[negocios.single]`) sirve un panel Streamlit, un frontend Astro y un backend, y cada negocio multi-tenant, lo mismo. Con la píldora Streamlit no salen, aunque su panel sea una app Streamlit, que es justo lo que se busca al filtrar por framework: abrir o repasar las apps de ese tipo. ADR-0015 descartó varios tipos por proyecto y dejó abierta la ampliación "si hace falta"; esta ADR la hace, a nivel de enlace. Una clave nueva del registro es código y lleva ADR ([0004](0004-registro-de-proyectos-como-dato.md)).

## Decisión

- **Clave `tipo` opcional en cada enlace de `enlaces`** (`[[proyecto]]` y `[negocios.single]`): texto libre, como el `tipo` de la fila, p. ej. `{ etiqueta = "Panel", puerto = 8505, tipo = "Streamlit" }`. Un enlace sin `tipo` hereda el de su fila.
- **Tipos de una fila**: el suyo más los de sus enlaces. Una fila sale con un filtro de tipo si alguno coincide con las píldoras activas. Las píldoras se siguen generando de los valores presentes, ahora también de los enlaces.
- **Enlaces visibles**: con un filtro de tipo activo, cada fila muestra solo los enlaces de los tipos activos. Sin filtro de tipo, o si la fila coincide por su propio tipo y el enlace lo hereda, salen todos. Heruka Life con Streamlit enseña solo Panel; con `heruka-flow`, los tres.
- **Negocios multi-tenant**: sus enlaces (Frontend · Panel · API) están en código, así que el tipo de su Panel también: `Streamlit`. La fila "Heruka Flow", que no tiene enlaces de servicio, sigue siendo solo `heruka-flow`.
- Matiza [ADR-0015](0015-tipo-de-aplicacion-en-el-registro.md): su alternativa "varios tipos por proyecto" se resuelve con tipos por enlace; el resto sigue igual.

## Alternativas descartadas

- **`tipos = [...]` en la fila**: la fila saldría con Streamlit, pero con sus tres enlaces; no dice cuál de ellos es la app Streamlit.
- **Cambiar el `tipo` de Heruka Life a Streamlit**: perdería la píldora `heruka-flow`, que agrupa los negocios ([ADR-0015](0015-tipo-de-aplicacion-en-el-registro.md)).
- **Una fila aparte para el panel**: un mismo proyecto saldría dos veces, con dos interruptores que arrancan lo mismo.

## Consecuencias

- Filtrar por un framework enseña todos sus servicios, también los que viven dentro de un proyecto multi-servicio, y solo esos enlaces.
- Con un filtro de tipo, el orden por la columna Enlaces sigue usando todos los enlaces de la fila, no solo los visibles.
- Un `tipo` de enlace mal escrito crea una píldora aparte, como el de fila.
- La demo (`demo/proyectos.toml`) gana `tipo` en algún enlace para enseñarlo.
- Docs a actualizar al implementar: [3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md) (`tipo` en `enlaces`) y [5 — Panel](../A1-Vision/5-panel-streamlit.md) (filtro por tipo). Tests de `config/proyectos.py` y del filtro de la Lanzadera.

## Estado

Aceptada (2026-11-05) — issue [#17](https://github.com/davidbp845/lanzadera/issues/17).

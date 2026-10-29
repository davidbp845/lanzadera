# 0014 — Proyectos sin app: `puerto` opcional y fila de solo enlaces

## Contexto

Cada `[[proyecto]]` del registro exige `puerto`, y una fila sin `cmd` se lee como la propia Lanzadera ("esta app"). Hay proyectos de `Data` que no sirven nada en un puerto, como un repositorio de documentación y skills con su propio tablero de GitHub, y de los que en la Lanzadera solo interesa el enlace al repo y al tablero, con sus pastillas de issues. Hoy no tienen fila: un puerto inventado los pintaría como "parado", con un interruptor que no arranca nada.

Dejar de exigir una clave del registro es código y lleva ADR ([0004](0004-registro-de-proyectos-como-dato.md)). Matiza [0003](0003-el-puerto-como-fuente-de-verdad.md): el puerto sigue siendo la fuente de verdad del estado, pero solo de los proyectos que tienen uno.

## Decisión

- `puerto` pasa a ser opcional en `[[proyecto]]`. Una entrada sin `puerto` es una **fila de solo enlaces**: no lleva `cmd`, `cmd_detener`, `enlaces`, `env` ni `intentos_espera_inicio`.
- En la Lanzadera, la fila muestra nombre y la columna GitHub (repo, tablero y pastillas del tablero); puerto, estado y enlaces van con "—" y no hay interruptor.
- Cuenta para los filtros de carpeta, el buscador, el orden por issues, el gráfico de issues y la actividad, que salen de su carpeta. Los filtros de estado (activo, parado) la dejan fuera: no tiene estado.
- No entra en Local: ni en la tabla de puertos ni en la medida de RAM.

## Alternativas descartadas

- **Un puerto inventado**: la fila sale como parada, con un interruptor que no hace nada, y el puerto aparece en Local como libre.
- **Una clave nueva (`tipo = "enlaces"`)**: dice lo mismo que la ausencia de `puerto`, y obliga a validar combinaciones incoherentes (tipo de enlaces con puerto).
- **Una fila en `datos/enlaces.csv`**: funciona sin código, pero se pierden las pastillas del tablero, el orden por issues y la pastilla de carpeta en la Lanzadera.

## Consecuencias

- Todo lo que lee `proyecto["puerto"]` tiene que contemplar `None`: estado, fila, buscador, Local y RAM.
- Ya no es un error de carga olvidar el `puerto` de un proyecto con app: sale como fila de solo enlaces. El fallo se ve en el panel (sin interruptor), no al leer el registro.
- Hay que actualizar `doc/A1-Vision/3-modelo-de-datos.md`, `doc/A1-Vision/5-panel-streamlit.md` y los tests de `config/proyectos.py` y de la Lanzadera.

## Estado

Aceptada (2026-10-29) — issue [#7](https://github.com/davidbp845/lanzadera/issues/7).

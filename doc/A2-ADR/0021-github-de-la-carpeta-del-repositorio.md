# 0021 — GitHub de cada fila desde la carpeta de su repositorio, no desde la de arranque

## Contexto

La columna GitHub de la Lanzadera, sus pastillas, el gráfico de issues y la actividad salen de `github.py` sobre la carpeta de cada fila: el `origin` de git y el tablero del `CLAUDE.md` con `## Método` más cercano. Para un `[[proyecto]]` esa carpeta es `ruta`, la misma que hace de `cwd` de `cmd`; para las filas de negocios, `[negocios] ruta`, la de heruka-flow ([ADR-0009](0009-negocios-como-filas-de-la-lanzadera.md)).

Las dos cosas no siempre coinciden:

- **Negocios multi-tenant**: el código es el de heruka-flow, pero cada negocio vive en una carpeta hermana con su id (su `business.yaml`, su vault y sus assets), que puede tener repositorio y tablero propios, solo repositorio o ninguno. Con ADR-0009 todas las filas de negocio enlazaban a heruka-flow, así que el tablero de un negocio no salía en ningún sitio y el de heruka-flow se contaba varias veces bajo el nombre de un negocio.
- **Proyectos que se arrancan desde el código de otro**: una landing que se sirve con el frontend de heruka-flow apuntado a su propia config (`env`), con su repositorio en otra carpeta; o `[negocios.single]`, que arranca heruka-flow en modo single-tenant para un negocio con repositorio y tablero propios. Su `ruta` tiene que ser la de heruka-flow para arrancar, y por eso enlazan al GitHub equivocado.

Una clave nueva del registro es código y lleva ADR ([0004](0004-registro-de-proyectos-como-dato.md)).

## Decisión

- **Negocios multi-tenant**: la carpeta de un negocio es la hermana de heruka-flow con su id (`<padre de [negocios] ruta>/<id>`), la convención de carpetas de heruka-flow. Cada fila de negocio enlaza al repositorio y al tablero de esa carpeta, con lo que tenga. Esas carpetas entran también en las pastillas, el gráfico de issues y la actividad. No hace falta clave: el id ya viene de `dev_up.sh --listar`.
- **La fila agregada se llama "Heruka Flow"** (antes "Todos los negocios"), en la Lanzadera y en Local, y enlaza al repositorio y al tablero de heruka-flow. En el gráfico de issues, el tablero de heruka-flow lleva ese nombre.
- **Clave opcional `ruta_github` en `[[proyecto]]` y en `[negocios.single]`**: carpeta, relativa a `Data` como `ruta`, de la que salen el repositorio y el tablero de la fila (columna GitHub, pastillas, orden por issues, gráfico de issues, actividad y página ADR). Sin ella, se usa `ruta`. Con `ruta_github = false`, la fila no tiene GitHub: es para un proyecto que es parte de otro sin repositorio ni tablero propios (p. ej. una consola que vive en la carpeta de heruka-flow), para que no repita el GitHub de la fila de ese otro ni se sume a su nombre en el gráfico de issues y en la página ADR. `ruta` sigue siendo el `cwd` de `cmd` y `cmd_detener` y la carpeta raíz de las píldoras.
- Matiza [ADR-0009](0009-negocios-como-filas-de-la-lanzadera.md): su punto **GitHub** queda superado por esta; el resto sigue igual.

## Alternativas descartadas

- **Que `dev_up.sh --listar` devuelva también la carpeta de cada negocio**: es lo más explícito, pero cambia el contrato de otro repo para un dato que la convención de carpetas hermanas ya da.
- **Una clave por negocio en el registro**: duplicaría en el registro la configuración de heruka-flow, lo que ya descartó [ADR-0005](0005-negocios-los-puertos-los-decide-heruka-flow.md).
- **Deducir la carpeta del repositorio del `env` del proyecto** (p. ej. de `CONFIG_PATH`): depende de cómo nombre cada proyecto sus variables y no sirve para `[negocios.single]`.
- **Una segunda fila sin app ([ADR-0014](0014-proyectos-sin-app-solo-enlaces.md)) para el repositorio**: funciona sin código, pero un mismo proyecto sale dos veces y la fila que se arranca sigue enlazando al GitHub equivocado.

## Consecuencias

- Cada fila enlaza al repositorio y al tablero de lo que representa, y un tablero de negocio cuenta en las pastillas y en el gráfico de issues con su nombre.
- Un negocio cuya carpeta no siga la convención (otro nombre que su id) sale sin GitHub, como una fila sin repositorio.
- La actividad suma los commits de los repositorios de los negocios y de los `ruta_github`, que antes no contaban.
- En la demo, cada negocio busca su GitHub por su id en `demo/estado.toml`.
- Docs a actualizar al implementar la clave: [3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md) (`ruta_github`) y [5 — Panel](../A1-Vision/5-panel-streamlit.md). Tests de `config/proyectos.py`.

## Estado

Aceptada (2026-11-02) — issue [#12](https://github.com/davidbp845/lanzadera/issues/12).

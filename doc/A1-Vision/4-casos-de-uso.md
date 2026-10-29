# 4. Casos de uso y comandos

## Uso diario (panel)

| Caso | Cómo |
|---|---|
| Ver qué está activo | Página "Lanzadera": semáforo por fila, o filtro "activo" |
| Encontrar un proyecto | Página "Lanzadera": buscador (nombre, ruta, puerto) y filtro por carpeta raíz |
| Ir al repositorio o al tablero, ver cuánto hay en cada estado | Página "Lanzadera": columna GitHub, con el recuento por estado del tablero |
| Arrancar un proyecto | Interruptor a "activo": espera a que respondan todos sus puertos antes de ponerse verde |
| Parar un proyecto | Interruptor a "parado" |
| Abrir un proyecto | Enlace(s) de su fila, visibles solo si está activo |
| Arrancar/parar negocios | Página "Lanzadera", filtro "Negocios": todos a la vez o uno a uno (rearranca el stack con la nueva selección) |
| Encontrar un enlace | Página "Enlaces": buscador de texto + filtro por etiquetas |
| Ver cuánto trabajo hay abierto y cuánta actividad | Página "Lanzadera": tarjetas de issues por estado y de actividad, plegables a la vez |
| Ver cuánta RAM gasta cada proyecto | Página "Local": indicadores, barra por proyecto y servicio, y la tabla en "Ver como tabla" |
| Cambiar de idioma | Lateral: `ES` / `EN` |
| Probar la demo de solo lectura | `HOME_LAUNCHER_DEMO=1 ./start.sh --server.port <libre>` (en `:8501` ya está el servicio) |

## Comandos de Claude Code (contenedor)

| Comando | Qué hace |
|---|---|
| `/dev:ayuda` | Lista los comandos disponibles, los del proyecto y los del método común |
| `/crear-enlace` | Añade una fila a `datos/enlaces.csv` con el módulo `csv` |
| `/crear-atajo` | Añade a `~/.bashrc` la función de atajo de un proyecto de `Data/` |
| `/uso-ram` | Tabla con la RAM real (RSS) de cada proyecto activo |

Ciclo de issues (nivel C, [metodología](../A0-Metodologia/metodologia-de-diseno-y-desarrollo.md)): los `/dev:*` del método común (plugin `dev@metodo`), con los datos del proyecto en la sección `## Método` del `CLAUDE.md` del contenedor: `/dev:crear-issue`, `/dev:detectar-bug`, `/dev:resolver-issue`, `/dev:sprint`, `/dev:cerrar-issue`, `/dev:crear-decision`, `/dev:nueva-vision`…

## Desde otras apps

| Caso | Cómo |
|---|---|
| Dar de alta un enlace | `python3 <lanzadera>/scripts/anadir_enlace.py "descripcion" "url" "etiquetas"` (contrato en [integraciones](6-integraciones.md#otras-apps-alta-de-enlaces)) |

## Trabajo de desarrollo

| Caso | Nivel |
|---|---|
| Dar de alta un proyecto estándar | Fila en `datos/proyectos.toml` + checklist [B3](../B3-Puesta-marcha/README.md) |
| Dar de alta un proyecto no estándar | Ficha [B1](../B1-Fichas-proyecto/README.md) + B2 + B3 |
| Cambiar cómo arranca un proyecto existente | Su ficha B1 y el script del proyecto hermano, no `app.py` |
| Página o comportamiento nuevo del panel | Nivel C |

# 3. Modelo de datos

Tres ficheros en `datos/` del contenedor, leídos vía `config/paths.py` (`HOME_LAUNCHER_DATOS` o `../datos`; en la demo, `demo/` del repo, con el mismo formato).

## Registro de proyectos — `datos/proyectos.toml`

Cargado por `config/proyectos.py:cargar()`. Las rutas son relativas a la carpeta `Data` (`HOME_LAUNCHER_RAIZ` o tres niveles por encima del repo; en la demo son ficticias y no se leen).

### `[[proyecto]]` — una fila de la página "Lanzadera", en orden

| Clave | Tipo | Obligatoria | Significado |
|---|---|---|---|
| `nombre` | texto | sí | Lo que se muestra |
| `slug` | texto | sí | Identificador estable (clave del interruptor en `st.session_state`) |
| `puerto` | entero | no | Puerto principal: el que decide el semáforo. Sin él, el proyecto no tiene app: su fila es solo de enlaces de GitHub, sin estado ni interruptor, y no entra en Local ([ADR-0014](../A2-ADR/0014-proyectos-sin-app-solo-enlaces.md)) |
| `ruta` | texto | sí | Carpeta del proyecto, relativa a `Data`; `cwd` de `cmd` y `cmd_detener` |
| `tipo` | texto | no | Framework principal de la app (`Streamlit`, `Astro`, `Wagtail`…), el del servicio del puerto principal. Cada valor distinto es una píldora de tipo en la Lanzadera; se muestra tal cual, así que `streamlit` y `Streamlit` serían dos ([ADR-0015](../A2-ADR/0015-tipo-de-aplicacion-en-el-registro.md)) |
| `cmd` | lista | no | Comando de arranque. Sin él, la fila es esta misma app (no se para desde sí misma) |
| `cmd_detener` | lista | no | Comando de parada. Sin él, `SIGTERM` al grupo de quien escucha `puerto` |
| `intentos_espera_inicio` | entero | no | Intentos de 0,5 s esperando a que los puertos respondan (por defecto 20 = 10 s) |
| `env` | tabla | no | Variables añadidas al entorno heredado (no lo sustituyen) |
| `enlaces` | lista de `{etiqueta, puerto, ruta_url?, host?}` | no | Varios servicios: un enlace por servicio, a `http://<host>:<puerto><ruta_url>` (`host` por defecto `localhost`; [ADR-0013](../A2-ADR/0013-host-opcional-en-los-enlaces.md)). `iniciar()` espera una vez a cada puerto, aunque se repita en varios enlaces |

Cada entrada no trivial lleva encima un comentario con el porqué de sus claves (p. ej. por qué necesita `cmd_detener`). Esos comentarios son parte del dato.

### `[negocios]` y `[negocios.single]`

Opcionales: solo tienen sentido con heruka-flow. Sin `[negocios]`, la Lanzadera no tiene filas de negocios ni píldora `heruka-flow`, y Local, la actividad y el gráfico de issues se quedan con los `[[proyecto]]`.

- `negocios.ruta`: carpeta de heruka-flow, donde se ejecutan `dev_up.sh`/`dev_down.sh`.
- `negocios.intentos_espera_inicio`: margen de arranque de cada negocio.
- `negocios.single`: un `[[proyecto]]` más, que sale como fila de negocio en la Lanzadera solo si heruka-flow no tiene negocios multi-tenant.

Las filas de negocios, multi-tenant o single, son tipo `heruka-flow` sin escribirlo en el registro.

En memoria, `cargar()` devuelve los proyectos como dicts con `path` (ruta absoluta), `puerto`, `cmd` y `tipo` (`None` si faltan) y `enlaces` como tuplas `(etiqueta, puerto, ruta_url, host)`, con `ruta_url` vacía y `host` `localhost` si faltan. La URL la construye `url_enlace()`.

## Enlaces — `datos/enlaces.csv`

| Columna | Significado |
|---|---|
| `descripcion` | Texto de la fila |
| `enlace` | URL (`http://` o `https://`) |
| `etiquetas` | Cero o más etiquetas separadas por `;` (`Heruka;Calendar`) |

Las etiquetas son libres. El color de cada una sale de una paleta fija por orden alfabético, así que puede cambiar al añadir una etiqueta nueva.

## Servidores — `datos/vps.toml`

Cargado por `config/vps.py:cargar()` para la página VPS ([ADR-0008](../A2-ADR/0008-pagina-vps-estado-por-ssh-bajo-demanda.md)). Si no existe, la página explica cómo crearlo.

### `[[vps]]` — un servidor; con más de uno, la página muestra un selector

| Clave | Tipo | Obligatoria | Significado |
|---|---|---|---|
| `nombre` | texto | sí | Lo que se muestra en el selector |
| `host` | texto | sí | Alias de `~/.ssh/config`. Usuario, puerto y clave viven allí: ninguna credencial entra en `datos/` |

## Estado de la demo — `demo/estado.toml` y `demo/vps.txt`

Solo en el modo demo ([ADR-0010](../A2-ADR/0010-demo-publica-de-solo-lectura.md)), leídos por `demo.py`. Sustituyen a lo que fuera de la demo se consulta al sistema:

| Clave | Sustituye a |
|---|---|
| `activos` | Puertos en escucha |
| `memoria_total_gb` | `MemTotal` de `/proc/meminfo` |
| `negocios` (`id`, `front`, `panel`, `api`) | `dev_up.sh --listar` |
| `[github.<slug>]` (`repo`, `cuenta` por estado); `negocios`, el de los negocios | Remoto git, tablero del `CLAUDE.md` y recuento con `gh` |
| `[ram]`, por slug: `{etiqueta, puerto?, mb}` por servicio | `ps` y `ss` |

`demo/vps.txt` es una salida de `scripts/estado_vps.sh`, con sus líneas `### <Sección>`.

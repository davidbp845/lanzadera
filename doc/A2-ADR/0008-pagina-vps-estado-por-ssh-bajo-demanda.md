# 0008 — Página VPS: estado por SSH bajo demanda, servidores en `datos/vps.toml`

## Contexto

El launcher solo mira lo local: puertos de `127.0.0.1` y procesos de esta máquina. Para saber cómo está el VPS (carga, memoria, disco, servicios caídos, contenedores) hay que abrir una terminal, entrar por SSH y lanzar a mano varios comandos.

Se quiere una página **VPS** en el panel que recupere lo más importante del estado del servidor en una sola llamada, lo muestre en fuente monoespaciada (tal cual lo devuelven los comandos) y tenga un botón **Refrescar** que repita la llamada. El servidor tiene que ser configurable, no una constante del código.

## Decisión

- **Servidores como dato**: `datos/vps.toml`, con un `[[vps]]` por servidor (`nombre`, `host`). `host` es un **alias de `~/.ssh/config`** (hoy, `vps`): usuario, puerto, clave y `ProxyJump` viven allí, no en `datos/`. Ninguna credencial entra en el contenedor ni en el submódulo. Se carga con `config/vps.py:cargar()` y su ruta sale de `config/paths.py:vps()`.
- **Una sola llamada SSH por consulta**: `ssh -o BatchMode=yes -o ConnectTimeout=5 <host> sh -s`, con un script remoto **fijo y de solo lectura** (`scripts/estado_vps.sh`) que se le pasa por la entrada estándar y no se instala en el servidor. Tiempo máximo total, 15 s. `BatchMode` hace que falle en vez de quedarse esperando una contraseña o la confirmación de una huella nueva.
- **Secciones fijas**: el script imprime bloques separados por una línea `### <Sección>`: Sistema (host, SO, kernel, uptime y carga) · Memoria (`free -h`) · Disco (`df -h`, sin tmpfs/overlay) · Servicios con fallo (`systemctl --failed`) · Procesos con más RAM (top 5) · Contenedores (`docker ps`, solo si hay docker) · Últimos accesos (`last -n 5`). Una sección cuyo comando no existe se omite en el propio script.
- **Bajo demanda, no vigilancia**: la consulta se hace al entrar en la página si no hay resultado guardado, y al pulsar **Refrescar**. El resultado (secciones, hora, duración, error) se guarda en `st.session_state` por servidor, para que los reruns de Streamlit no repitan la llamada.
- **Presentación**: cada sección con su subtítulo y su salida en `st.code(..., language=None)` (monoespaciada, con botón de copiar). Encima, estado de la conexión, hora de la última consulta y duración. Si falla, `st.error` con el `stderr` de ssh y se conserva el último resultado bueno marcado como antiguo.
- **Código**: la llamada y el troceado en secciones, en un módulo `vps.py` con tests propios (primer paso de [ADR-0007](0007-estructura-plana-sin-hexagonal.md) si `app.py` crece); `app.py` solo pinta la página.

## Alternativas descartadas

- **Usuario, IP y clave en `datos/vps.toml`**: duplicaría `~/.ssh/config` y metería datos de acceso en el contenedor, que se copia en la copia de seguridad.
- **Comandos configurables en el TOML**: el panel ejecutaría en el servidor lo que diga un fichero de datos. Con un script fijo en el repo, lo que se ejecuta en remoto se revisa en un diff y es siempre de solo lectura.
- **Paramiko / fabric**: una dependencia más para lo que ya hace el `ssh` del sistema, que además respeta `~/.ssh/config` y el agente sin configuración extra.
- **Agente o exportador en el VPS (node_exporter, Netdata, Glances API)**: obliga a instalar y exponer un servicio en el servidor; el objetivo es un vistazo puntual, no monitorización.
- **Una llamada SSH por sección**: varias conexiones por refresco y estados mezclados de instantes distintos.
- **Refresco automático periódico**: sería vigilancia continua, fuera de alcance ([7 — Fuera de alcance](../A1-Vision/7-fuera-de-alcance.md)).

## Consecuencias

- El launcher pasa a hablar con una máquina remota: su visión (A1) se amplía de "apps locales" a "apps locales y estado del VPS". Al implementar se actualizan [1 — Problema](../A1-Vision/1-problema-que-resuelve.md), [3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md) (`datos/vps.toml`), [5 — Panel](../A1-Vision/5-panel-streamlit.md) (cuarta página) y [6 — Integraciones](../A1-Vision/6-integraciones.md) (SSH).
- Requiere que `ssh <host>` funcione sin interacción desde la sesión de `home-streamlit.service` (clave sin frase o agente accesible desde systemd de usuario). Si no, la página lo dice con el error de ssh; no pide contraseñas.
- El panel sigue escuchando solo en `127.0.0.1`: quien ve la página ya tiene acceso SSH al VPS desde esta máquina.
- Los tests no abren conexiones: se prueba el troceado de la salida, el cargador con un fixture y la página con `AppTest` sustituyendo la llamada a `ssh`.
- Sin `datos/vps.toml` (o vacío), la página muestra cómo añadir un servidor en vez de fallar.

## Estado

Aceptada (2026-10-23). Implementación: [#1](https://github.com/davidbp845/home/issues/1).

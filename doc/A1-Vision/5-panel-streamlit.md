# 5. Panel Streamlit

`app.py`, servido en `:8501` (`.streamlit/config.toml`: solo `127.0.0.1`, tema claro, `headless`). Las cuatro páginas van en `layout="wide"`, fijado en una sola `st.set_page_config` al principio.

## Lateral e idioma

- Menú con las cuatro páginas (`st.radio`, `key="pagina"`) y, debajo, el idioma: `ES` / `EN` (`st.segmented_control`, `key="idioma"`). Empieza en el de `HOME_LAUNCHER_IDIOMA`; sin ella, inglés en la demo y español fuera.
- Todo texto visible sale de `textos.py`, un diccionario por idioma con las mismas claves (lo comprueba un test). Los valores internos (páginas, filtros) no cambian con el idioma: solo su `format_func`. Los números van con coma decimal en español y con punto en inglés.
- Los títulos de las secciones del VPS se traducen por su título en `estado_vps.sh`; lo que imprime cada comando, no.

## Lanzadera

- Arriba, dos tarjetas de gráficos (Altair) en dos columnas:
  - **Issues abiertos por estado**: una barra apilada por tablero (Backlog · Ready · In progress · In review, sin Done), de más a menos, con el total al final. Si varios proyectos comparten tablero, cuenta una vez y la etiqueta junta sus nombres con « · »; si no cabe, se resume (alias entre paréntesis, "+N" por los que no caben, "…"), y el tooltip los da completos. Sale de los mismos recuentos que las pastillas.
  - **Actividad**: mapa de calor de commits por día de las últimas 26 semanas, una columna por semana, en la rampa azul (gris sin commits), con los cortes en los quintiles de los días con commits para que no se sature con mucha actividad. Suma `git log --all --format=%cs` de cada carpeta del registro y de sus submódulos, sin repetir repositorio (`actividad.py`), cacheado una hora.
  - Cada tarjeta tiene su botón de plegar, pero las dos se pliegan y despliegan a la vez; plegadas, enseñan una línea de resumen. Al entrar están desplegadas, y el estado se guarda en una clave propia de `st.session_state` (`graficos_lanzadera`), no en la de un widget, para que siga igual al volver de otra página.
- Encima de la tabla, en una sola fila centrada verticalmente: buscador de texto (nombre, ruta o puerto), un solo grupo de píldoras con las carpetas raíz (`Apps`, `HerukaLife`…), los tipos de aplicación (uno por valor de `tipo` en el registro, en orden alfabético, más `heruka-flow` para las filas de negocios) y los estados (activo, parado), y **Actualizar tableros**. Debajo, en su propia línea, el contador "N de M", seguido de lo que lo explica (texto buscado, píldoras de filtro y de orden activas, separados por « · »), y cinco píldoras de orden (`↓ Backlog` … `↓ Done`, una sola a la vez, con el color de su estado; la activa, en blanco sobre su color oscurecido hasta 4,5:1): con una activa, la tabla se queda con las filas que tienen tablero, ordenadas de más a menos issues en ese estado. Las píldoras de carpeta y de tipo llevan la paleta de Enlaces, por CSS sobre su posición en el grupo (`st.pills` no admite un color por opción); la paleta tiene ocho colores, así que carpetas y tipos juntos no deberían pasar de ocho. Las de estado, el estilo de Streamlit. Dentro de carpetas, tipos y estados, OR; entre ellos y con el buscador, AND. Con un tipo activo, las filas sin `tipo` quedan fuera.
- El buscador es un componente propio (`st.components.v2`) que manda el texto mientras se escribe, con 250 ms de pausa, sin esperar a Intro: `st.text_input` solo avisa al pulsar Intro o al salir del campo. En `AppTest` no se teclea: se le da su estado en `session_state["buscar_proyecto"]`.
- Una fila de cabecera y una fila `st.columns` por `[[proyecto]]` o negocio visible: **proyecto** | puerto | estado | enlaces | GitHub | interruptor. No es HTML propio como Enlaces porque cada fila lleva un `st.toggle`. Cada fila va en un `st.container` con `key`, todas dentro de uno sin hueco entre hijos; un `<style>` sobre sus clases `st-key-*` da fondo a la cabecera (el primario, suave) y a las filas impares (efecto cebra), anula el `margin-bottom` negativo de los markdown de la fila y no deja partir puerto, estado ni interruptor. Los interruptores no llevan etiqueta visible: el estado ya está en su columna.
- Estado: `🟢 activa` (esta app), `🟢 activo` o `⚪ parado`. Enlaces: `abrir` o uno por servicio, solo si está activo. Un proyecto sin `puerto` (sin app, [ADR-0014](../A2-ADR/0014-proyectos-sin-app-solo-enlaces.md)) lleva "—" en puerto, estado, enlaces e interruptor y solo la columna GitHub; los filtros activo y parado lo dejan fuera. Si tiene `proceso` ([ADR-0017](../A2-ADR/0017-lanzadera-en-windows-y-proyectos-sin-puerto.md)), lleva "—" en puerto y enlaces, y estado e interruptor como cualquier proyecto con app.
- GitHub (`github.py`, cacheado una hora con `st.cache_data`): **repositorio**, el `origin` de la carpeta del proyecto o, si no tiene, el del primer submódulo de su `.gitmodules`; **tablero**, la línea `Tablero` de la sección `## Método` del `CLAUDE.md` más cercano subiendo desde su carpeta, sin pasar de `Data/`. Sin ninguno de los dos, `—`.
- Junto a "tablero", en la misma línea (`white-space: nowrap`), cinco pastillas con los items no archivados por estado, en orden Backlog · Ready · In progress · In review · Done (el nombre, en el tooltip de cada una); un cero va en gris. Los colores de estado son los cinco primeros de la paleta categórica validada (azul, naranja, aqua, amarillo, magenta), los mismos en pastillas, píldoras de orden y gráfico; el número va en texto oscuro sobre el color, porque amarillo y aqua no llegan a 3:1 como color de texto. Son HTML propio porque las de markdown no dejan cambiar tamaño ni ancho. La de *In progress* parpadea mientras una sesión de Claude Code trabaja en uno de sus issues (latido de menos de 15 minutos en el campo `Latido` del tablero, [ADR-0016](../A2-ADR/0016-latido-del-issue-en-curso.md)), con un borde oscuro de 2 px por dentro y esos issues en su tooltip; con `prefers-reduced-motion`, el borde sin parpadeo. Como el resto del recuento, puede tardar hasta 10 minutos en salir o irse. `github.recuento()` hace una consulta GraphQL de solo lectura por tablero con `gh api graphql`, todas en paralelo, cacheadas 10 minutos; **Actualizar tableros**, al final de la barra de filtros, vacía las dos cachés, la de los recuentos y la del repositorio y el tablero de cada fila, así que también saca un tablero recién añadido a un `CLAUDE.md`. Si `gh` falla (sin red o sin sesión), no salen las pastillas y el resto de la fila sigue igual; ese fallo no se guarda en la caché, así que en cuanto vuelve la red las pastillas salen en el siguiente rerun.
- El interruptor llama a `iniciar()` o `detener()` en su `on_change` y espera a que el puerto (o, sin puerto, su `proceso`) cambie antes del siguiente rerun, para que el semáforo no enseñe el estado viejo.

### Negocios en la Lanzadera

Filas de la misma tabla, detrás de los proyectos ([ADR-0009](../A2-ADR/0009-negocios-como-filas-de-la-lanzadera.md)), con carpeta `HerukaLife` y el GitHub de heruka-flow. Son tipo `heruka-flow`, que es su píldora. Solo si el registro tiene `[negocios]`; sin ella no hay filas de negocios ni píldora `heruka-flow`:

- Si `dev_up.sh --listar` devuelve negocios: una fila "Todos los negocios" (sus ids activos en Enlaces) y una por negocio ("Negocio `<id>`", con su puerto de panel y enlaces a Frontend, Panel y API).
- Como un solo backend (`:8000`) sirve a todos, cambiar un interruptor para el stack entero y lo vuelve a levantar con los elegidos.
- Si no hay negocios multi-tenant: una sola fila, `[negocios.single]` (Heruka Life), como un proyecto.
- `--listar` se guarda 60 s con `st.cache_data` (el buscador relanza la página al escribir) y se invalida al arrancar o parar negocios. Un negocio nuevo lanzado desde fuera tarda hasta ese tiempo en salir; el semáforo, no, porque sale del puerto.

## Enlaces

- En ancho, para que se lea la URL completa.
- HTML propio con `st.html(..., unsafe_allow_javascript=True)`: buscador, botones de etiqueta (OR entre las activas) y contador.
- El JS va en una IIFE: el documento persiste al navegar entre páginas y, sin ella, al volver se redeclararían variables globales y el filtro dejaría de funcionar ([Z-Anexos](../Z-Anexos/3-lecciones-aprendidas.md)).
- Todo el texto del CSV se escapa con `html.escape`.

## VPS

- Estado de cada servidor de `datos/vps.toml` ([ADR-0008](../A2-ADR/0008-pagina-vps-estado-por-ssh-bajo-demanda.md)): una sola llamada `ssh -o BatchMode=yes <host> sh -s` con el script fijo y de solo lectura `scripts/estado_vps.sh`, troceada en secciones por sus líneas `### <Sección>` (`vps.py`).
- Las secciones van en una rejilla de tres filas, colocadas por título (`vps.FILAS`): Sistema · Memoria · Servicios con fallo, Disco · Procesos con más RAM, y Contenedores · Últimos accesos. Así caben sin scroll a 1920×1080. Una sección que el servidor no imprime deja su hueco, y una que no está en `FILAS` va en una fila al final.
- Cada sección lleva su título en negrita y su salida en `st.code` (monoespaciada), con las líneas largas partidas en vez de scroll horizontal. Memoria enseña solo total, used, free y available de `free -h`, para que quepa en su columna.
- Encima, `● conectado` / `● sin conexión`, el alias, la hora y la duración de la consulta, y el botón **Refrescar**.
- Entre esa línea y la rejilla, una fila de indicadores leídos de las mismas secciones (`vps.medidores`), sin ejecutar nada más en el servidor: memoria usada sobre el total, disco `/` (`Use%`), carga a 1 min sobre el número de CPU, y servicios con fallo. Los tres primeros llevan medidor: azul, naranja desde 80 % y rojo desde 90 %, con "⚠ alto" en el texto para no depender solo del color. Lo que no se pueda leer no sale.
- Se consulta al entrar por primera vez y al refrescar; el resultado se guarda en `st.session_state["vps"]` para que los reruns no repitan la llamada.
- Si falla: `st.error` con el `stderr` de ssh y, si la hubo, la última consulta correcta marcada como antigua.

## Local

- RAM real (RSS) de cada proyecto activo, medida por `ram.py` con el mismo método que `/uso-ram`: una lectura de procesos y otra de puertos en escucha, con `psutil`; de cada proyecto con `cmd`, los descendientes de sus raíces reales (procesos que ejecutan su `cmd`, solo o tras un intérprete, con `cwd` en su carpeta; todas las instancias si hay varias) más los descendientes del proceso de cada puerto raíz; de Home, solo su proceso; de un proyecto con `proceso`, los procesos que lo llevan en su línea de comando y sus descendientes.
- Mide los `[[proyecto]]` del registro que tienen `puerto` y, si el registro tiene `[negocios]`, una fila de heruka-flow: "Todos los negocios" si `dev_up.sh --listar` devuelve negocios, y si no `[negocios.single]`. Los dos modos se excluyen, así que nunca salen las dos. Un proyecto cuenta como activo si algo escucha su puerto principal.
- "Todos los negocios" no tiene puerto principal: cuenta como activo si escucha el frontend, el panel o la API de algún negocio. Sus raíces reales son los `dev_up.sh` de heruka-flow, y sus puertos raíz, los de cada negocio. El desglose lleva el frontend y el panel de cada negocio ("Negocio `<id>` · Frontend"…) y una sola línea, "Backend común", con el puerto de la primera API: un mismo proceso sirve las APIs de todos los negocios. `--listar` sale de la misma caché de 60 s que la Lanzadera.
- Si el proceso del puerto es de otro usuario (Docker como root), `psutil` no da su PID: el proyecto sale al final con RAM "no visible", fuera del total, y un `st.info` lo explica.
- Tres indicadores: RAM total (con medidor sobre la RAM de la máquina, de `psutil`), proyectos activos sobre los del registro, y el que más usa con su parte del total.
- **RAM por proyecto**: barra apilada de mayor a menor, un tramo por servicio en los multi-servicio (tooltip con el servicio y su RAM), con el total al final. Al lado, **Puertos**: los del registro (principal, los de `enlaces` y los de los negocios), en verde los que tienen algo escuchando.
- En el desplegable "Ver como tabla", la tabla Proyecto · Puerto · RAM, de mayor a menor, con fila de total, y la RAM de cada servicio de los proyectos con `enlaces`, con una línea "Script de arranque" para lo que no cuelga de ningún puerto (el script y los wrappers por encima del proceso del puerto). Sin puerto principal, la columna Puerto va vacía.
- Si dos proyectos comparten procesos, `st.warning`: su RAM se está contando dos veces.
- Se mide al entrar por primera vez y al pulsar **Recalcular**; el resultado se guarda en `st.session_state["ram"]`. Solo lee procesos: no arranca ni para nada.

## Modo demo

Con `HOME_LAUNCHER_DEMO=1` el panel es la demo pública de solo lectura ([ADR-0010](../A2-ADR/0010-demo-publica-de-solo-lectura.md)):

- Datos de `demo/` del repo (`proyectos.toml`, `enlaces.csv`, `vps.toml`) en vez de `../datos`, y el estado que fuera de la demo se consulta al sistema, de `demo/estado.toml` (puertos en escucha, negocios, GitHub, RAM) y `demo/vps.txt` (salida de `estado_vps.sh`). La actividad se genera, siempre igual para cada día (`demo.py`).
- Ninguna función que consulte el sistema llega a ejecutarse: puertos, procesos, `gh`, `git`, `dev_up.sh`, `dev_down.sh` y SSH devuelven los datos de ejemplo, y arrancar o parar no hace nada.
- Un aviso azul arriba de cada página; interruptores deshabilitados con tooltip; los enlaces a `localhost` y a GitHub salen como texto punteado con tooltip, no como enlace. En el lateral, un enlace al repo para usarla en local.

Capturas y mockups, en [C3](../C3-Diseno-UX-UI/README.md).

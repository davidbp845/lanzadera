# Metodología de diseño y desarrollo de home

Metodología en tres niveles para un proyecto pequeño:
-  una sola aplicación (el launcher)
-  un solo usuario
-  ejecutándose en local, con Claude Code como operador.

Adaptada de la de `emailmanage` (y esta, de las de `namesyncia` y `movimientos`), que tienen el mismo esqueleto: contenedor local con los datos + submódulo con código y documentación.

Es un guion de arranque, no una norma cerrada. Cada etapa se describe con:
- **Documento**
- **Índice** (secciones esperadas)
- **Resultado** (qué queda al terminar)
- **Columna de kanban** (proyecto GitHub #9, campo Status: Backlog/Ready/In progress/In review/Done)
- **Skill/comando de Claude Code** si existe uno. Los `/dev:*` son los del método común (plugin `dev@metodo`), que toman los datos del proyecto de la sección `## Método` del `CLAUDE.md` del contenedor.

### Por qué estos tres niveles

- **A — Visión y arquitectura**: hay una visión (un único sitio desde el que arrancar, parar y abrir todo lo local) y decisiones que merecen ADR (cómo se arranca y para cada proyecto, cómo se sabe si está activo, dónde vive el registro).
- **B — Alta de proyecto**: el eje de extensión de home son los *proyectos hermanos*. Casi todos los cambios del historial son "Launcher: añade X". La mayoría encajan en el patrón estándar (un puerto, `./start.sh`), pero los que no (varios servicios, Docker, systemd, arranques lentos) necesitan pensar antes cómo se arrancan, se paran y se sabe que están listos.
- **C — Ciclo de feature/issue**: el día a día: páginas del panel, bugs, retoques. C3 se limita al panel Streamlit.

**Lo que NO es un nivel de trabajo**: añadir un enlace (`/crear-enlace`), arrancar o parar un proyecto, mirar la RAM (`/uso-ram`). Eso es *uso*: sus efectos, si los hay, se versionan en el contenedor (`datos/`). Tampoco lo es dar de alta un proyecto que sigue el patrón estándar: basta su fila en `datos/proyectos.toml` y la checklist B3, sin ficha.

## Los tres niveles de trabajo

| Nivel | Qué decide | Frecuencia | ¿Vive en el kanban? |
|---|---|---|---|
| **A. Visión y arquitectura** | Qué hace el launcher, modelo de datos, decisiones que afectan a todo | Baja | No directamente: genera issues B/C |
| **B. Alta de proyecto** | Cómo se arranca, se para y se sabe que está listo un proyecto | Por proyecto nuevo o cambio de arranque | Un issue por proyecto no estándar |
| **C. Feature/issue** | Una funcionalidad, un bug, un retoque | Continua | Sí, 1:1 con las columnas |

---

## Nivel A — Visión y arquitectura

### A1. Visión y alcance

- **Documento**: documento de visión, vivo: un fichero por elemento del índice en `doc/A1-Vision/`.
- **Índice** (ver [A1-Vision](../A1-Vision/README.md)): problema que resuelve · entradas y salidas · modelo de datos · casos de uso y comandos · páginas del panel · integraciones · fuera de alcance · métricas de éxito · riesgos · ampliaciones futuras.
- **Resultado**: documentos de referencia que no se "cierran": se actualizan cuando cambia la visión y alimentan el Backlog.
- **Kanban**: no aplica directamente; cuando algo madura en trabajo accionable nace un issue en **Backlog**.
- **Skills**: `/dev:nueva-vision`

### A2. Decisiones de arquitectura (ADR)

- **Documento**: `doc/A2-ADR/NNNN-titulo-corto.md`, un fichero por decisión (patrón ADR de Nygard).
- **Índice**: Contexto · Decisión · Alternativas descartadas · Consecuencias · Estado (propuesta / aceptada / superada por ADR-N).
- **Resultado**: fichero versionado, citado desde el código o desde el issue de implementación.
- **Kanban**: se redacta en **Ready** del issue que la origina, o genera su propio issue de implementación.
- **Skills**: `Plan` (subagente arquitecto) · `/dev:crear-decision` · `/code-review`

---

## Nivel B — Alta de proyecto en el launcher

Un *proyecto* es una fila de la página "Lanzadera": algo local con un puerto, un comando de arranque y, si hace falta, uno de parada ([3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md)).

El disparador es práctico: hay un proyecto hermano nuevo (o uno existente cambia su forma de arrancar) y se quiere tener en el launcher.

### B1. Ficha de proyecto

Solo para proyectos **no estándar**: los que no se arrancan con un único `./start.sh` y se paran matando a quien escucha su puerto.

- **Documento**: `doc/B1-Fichas-proyecto/<n>-<slug>.md`, redactada **antes** de añadir la fila.
- **Índice**:
	1. Qué es y dónde vive (ruta, repo, si es submódulo)
	2. Servicios y puertos (cuál es el principal y por qué)
	3. Arranque (comando, entorno, si es interactivo, si hay servicio de systemd)
	4. Parada (por qué no basta matar por puerto, si es el caso)
	5. Tiempo hasta estar listo (medido, no supuesto: logs) y margen de espera
	6. Choques conocidos (puertos, procesos ajenos que no hay que matar)
	7. Verificación (cómo se comprueba que el toggle refleja la realidad)
- **Resultado**: ficha archivada + fila en `datos/proyectos.toml` con un comentario que resuma el porqué de sus claves.
- **Kanban**: **Backlog**: issue "Proyecto: `<nombre>`". Un solo issue para B1–B3.
- **Skills**: ninguno propio aún.

### B2. Diseño técnico del alta

- **Documento**: sección "Diseño técnico" en el issue; fichero en `doc/B2-Disenos-tecnicos/` solo si no cabe. ADR si obliga a añadir una **clave nueva** al registro o a cambiar `iniciar()`/`detener()`.
- **Índice**: claves del registro que usa · scripts que hay que crear **en el proyecto hermano** (no en home, ver [ADR-0002](../A2-ADR/0002-arranque-y-parada-delegados-en-cada-proyecto.md)) · choques de puertos · efecto sobre `/uso-ram`.
- **Resultado**: plan validado en el issue.
- **Kanban**: **Ready**.

### B3. Puesta en marcha

- **Documento**: checklist única en `doc/B3-Puesta-marcha/README.md`.
- **Resultado**: el toggle arranca y para el proyecto de verdad, los enlaces aparecen solo cuando responde, `/uso-ram` lo mide y tiene atajo de terminal.
- **Kanban**: **In progress** → **In review** → **Done**.

---

## Nivel C — Ciclo de feature/issue

El detalle de cada etapa vive en el issue y su estado, en el [tablero (proyecto GitHub #9)](https://github.com/users/davidbp845/projects/9), que es el único índice de issues. Las carpetas `doc/C*/` solo describen su etapa.

### C1. Análisis — **Backlog**
- **Documento**: cuerpo del issue.
- **Índice**: situación/diagnóstico · plan · alcance (`app.py` / `config/` / `datos/` / scripts de un proyecto hermano) · tests existentes que el plan puede dejar obsoletos.
- **Etiquetas**: una de área y, si es un bug, `bug`.

| Etiqueta | Qué cubre |
|---|---|
| `proyectos` | Registro de proyectos, arranque, parada y semáforo (nivel B incluido) |
| `negocios` | Filas de negocios de la Lanzadera e integración con `dev_up.sh` de heruka-flow |
| `enlaces` | Página "Enlaces" y `datos/enlaces.csv` |
| `panel` | Aspecto y navegación del panel Streamlit |
| `infra` | `config/`, dependencias, tests/ruff, `start.sh`/`stop.sh`, servicio de systemd |
| `documentation` | Solo documentación: visión, ADR, metodología, comandos de Claude Code |

- **Skills**: `/dev:crear-issue` · `/dev:detectar-bug`

### C2. Diseño técnico — **Backlog → Ready**
Solo si el issue cambia el formato del registro, `iniciar()`/`detener()` o afecta a más de una página.
- **Índice**: claves o funciones afectadas · proyectos del registro a los que afecta · alternativas descartadas · tests a añadir.
- **Skills**: `/dev:resolver-issue` y `/dev:sprint` (si el issue lo necesitaba y no lo tiene, añaden el comentario "Diseño técnico" antes de implementar) · `Plan` · `/code-review` tras implementar

### C3. Diseño UX/UI — **Ready**
Solo si el issue cambia lo que se ve en el panel.
- **Índice**: página(s) afectadas · estado antes/después · qué acciones arrancan o paran procesos.
- **Skills**: `dev:developing-with-streamlit` · captura o `Artifact` (mockup) si el cambio lo merece; las capturas se guardan en `doc/C3-Diseno-UX-UI/`.

### C4. Implementación — **In progress**
- **Resultado**: commit local en el submódulo, `pytest` en verde, `ruff check .` y `ruff format --check .` limpios.
- **Skills**: `/dev:sprint` · `/dev:resolver-issue` · `dev:developing-with-streamlit`

### C5. Verificación — **In progress → In review**
- **Índice**: tests automáticos ejecutados · prueba manual en el panel (arrancar y parar los proyectos afectados) · `AppTest` de las páginas sin excepciones · capturas si es visual.
- **Skills**: `/run`

### C6. Revisión — **In review**
- **Índice**: hallazgos por severidad · veredicto.
- **Skills**: `/code-review` · `/simplify`

### C7. Cierre — **Done**
- **Documento**: comentario de cierre + el aprendizaje, si lo hay, en su sitio:
	- conocimiento **de un proyecto hermano** (cómo arranca, cuánto tarda) → su ficha B1, el comentario de su fila en `datos/proyectos.toml` o, mejor, la documentación de ese proyecto;
	- conocimiento **del launcher** → `doc/A1-Vision/` o `doc/Z-Anexos/`;
	- conocimiento **técnico reusable** → `conocimiento/vault_in/`;
	- **regla de colaboración** con Claude → memoria de Claude Code.
- **Skills**: `/dev:cerrar-issue`

  El flujo termina en **In review**; el paso a **Done** lo hace el usuario.

## Tabla resumen (Nivel C)

| Etapa | Documento | Kanban | Skill |
|---|---|---|---|
| C1 Análisis | Cuerpo del issue | Backlog | `/dev:crear-issue` |
| C2 Diseño técnico | Comentario "Diseño técnico" / ADR | Backlog→Ready | `Plan`, `/dev:resolver-issue` |
| C3 Diseño UX/UI | Mockup / descripción | Ready | `dev:developing-with-streamlit` |
| C4 Implementación | Código + tests | In progress | `/dev:sprint`, `/dev:resolver-issue` |
| C5 Verificación | Comentario de verificación | In progress→In review | `/run` |
| C6 Revisión | Hallazgos | In review | `/code-review`, `/simplify` |
| C7 Cierre | Comentario + aprendizaje archivado | Done | `/dev:cerrar-issue` |

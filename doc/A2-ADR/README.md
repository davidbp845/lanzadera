# A2 — Decisiones de arquitectura (ADR)

Nivel A2 de la [metodología](../A0-Metodologia/metodologia-de-diseno-y-desarrollo.md). Un fichero por decisión: Contexto · Decisión · Alternativas descartadas · Consecuencias · Estado.

Salvo la 0001 y la 0004 (tomadas al aplicar la metodología), recogen decisiones que ya estaban en el código y en su historial.

## Decisiones

| ADR | Decisión | Estado |
|---|---|---|
| [0001](0001-contenedor-local-con-los-datos.md) | Contenedor local con los datos; código y documentación, submódulo | Aceptada; el submódulo `home`, superado por 0012 |
| [0002](0002-arranque-y-parada-delegados-en-cada-proyecto.md) | Arranque y parada delegados en el script o servicio de cada proyecto | Aceptada |
| [0003](0003-el-puerto-como-fuente-de-verdad.md) | El puerto como fuente de verdad del estado | Aceptada; ampliada por 0017 (proyectos sin puerto, `psutil`, parada en Windows) |
| [0004](0004-registro-de-proyectos-como-dato.md) | Registro de proyectos como dato (`datos/proyectos.toml`) | Aceptada |
| [0005](0005-negocios-los-puertos-los-decide-heruka-flow.md) | Negocios: los puertos los decide heruka-flow | Aceptada; la página propia, superada por 0009 |
| [0006](0006-el-launcher-como-servicio-de-systemd.md) | El launcher como servicio de usuario de systemd | Aceptada; en Windows, `start.cmd` desde Inicio (0017) |
| [0007](0007-estructura-plana-sin-hexagonal.md) | Estructura plana (`app.py` + `config/`), sin hexagonal | Aceptada |
| [0008](0008-pagina-vps-estado-por-ssh-bajo-demanda.md) | Página VPS: estado por SSH bajo demanda, servidores en `datos/vps.toml` | Aceptada |
| [0009](0009-negocios-como-filas-de-la-lanzadera.md) | Negocios como filas de la Lanzadera, sin página propia | Aceptada; la píldora Negocios, superada por 0015 |
| [0010](0010-demo-publica-de-solo-lectura.md) | Demo pública de solo lectura con datos de ejemplo (`HOME_LAUNCHER_DEMO`) | Aceptada |
| [0011](0011-licencia-mit.md) | Licencia MIT para el repo | Aceptada |
| [0012](0012-lanzadera-sustituye-a-home.md) | El repo público `lanzadera` sustituye a `home`, que se archiva | Aceptada |
| [0013](0013-host-opcional-en-los-enlaces.md) | Host opcional en los enlaces de un proyecto (`admin.localhost`) | Aceptada |
| [0014](0014-proyectos-sin-app-solo-enlaces.md) | Proyectos sin app: `puerto` opcional y fila de solo enlaces | Aceptada; sin `puerto` pero con `proceso`, ampliada por 0017 |
| [0015](0015-tipo-de-aplicacion-en-el-registro.md) | Clave `tipo` en el registro y píldoras por tipo de aplicación (`heruka-flow` sustituye a Negocios) | Aceptada |
| [0016](0016-latido-del-issue-en-curso.md) | Latido del issue en curso en el campo `Latido` del tablero: la pastilla In progress parpadea | Aceptada |
| [0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md) | Lanzadera en Windows: clave `proceso` para proyectos sin puerto, `psutil` en los dos sistemas, `start.cmd` desde Inicio | Propuesta |

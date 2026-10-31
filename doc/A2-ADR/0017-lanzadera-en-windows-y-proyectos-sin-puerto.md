# 0017 — Lanzadera en Windows y proyectos sin puerto

## Contexto

La Lanzadera también tiene que funcionar en Windows, con sus propios proyectos. Hoy depende de Linux en cada pieza que mira el sistema: `ss -H -ltnp` para saber quién escucha un puerto, `ps` para la RAM, `/proc` para la carpeta de cada proceso y la memoria total, `SIGTERM` al grupo de procesos para parar ([0003](0003-el-puerto-como-fuente-de-verdad.md)) y un servicio de usuario de systemd para arrancar el propio launcher ([0006](0006-el-launcher-como-servicio-de-systemd.md)).

Además, en Windows hay proyectos que corren sin escuchar en ningún puerto, como un script de AutoHotkey que se queda residente. Según [0003](0003-el-puerto-como-fuente-de-verdad.md) el estado lo decide el puerto, y según [0014](0014-proyectos-sin-app-solo-enlaces.md) una entrada sin `puerto` es una fila de solo enlaces, sin estado ni interruptor. Ninguna de las dos cubre un proyecto que se arranca y se para pero no tiene puerto.

## Decisión

- **Proyectos sin puerto.** Clave opcional nueva `proceso` en `[[proyecto]]`: un texto que aparece en la línea de comandos del proceso del proyecto (por ejemplo, el nombre de su script). Una entrada con `proceso` y sin `puerto` está **activa** si algún proceso del usuario contiene ese texto en su línea de comandos. Tiene `cmd`, interruptor y semáforo como cualquier proyecto con app; no tiene `enlaces`. En Local, su RAM es la de esos procesos y sus hijos. Una entrada sin `puerto` ni `proceso` sigue siendo de solo enlaces ([0014](0014-proyectos-sin-app-solo-enlaces.md)).
- **Medición con `psutil` en los dos sistemas.** Conexiones en escucha, PID que escucha cada puerto, RAM, carpeta y línea de comandos de cada proceso, y memoria total salen de `psutil`, que sustituye a `ss`, `ps` y `/proc`. Hay una sola implementación. Un puerto de otro usuario sigue saliendo como activo sin RAM, igual que con `ss`.
- **Parada sin `cmd_detener`.** En Linux, como hasta ahora: `SIGTERM` al grupo de procesos del PID encontrado (por puerto o por `proceso`). En Windows no hay grupos de sesión: se termina el proceso y sus hijos con `psutil` (`terminate`, y `kill` a los que sigan vivos tras la espera). En Windows, `cmd` se lanza con `CREATE_NEW_PROCESS_GROUP` en lugar de `start_new_session=True`.
- **Arranque y parada delegados en el proyecto**, como en [0002](0002-arranque-y-parada-delegados-en-cada-proyecto.md): en Windows, `cmd` es el script o ejecutable del propio proyecto (`.cmd`, `.ps1`, el intérprete con su script), nunca un `start.sh`.
- **El launcher en Windows.** Un `start.cmd` en el repo lanza Streamlit con un entorno virtual propio de Windows, `venv-windows/`, fuera de git, porque `venv/` es el de Linux y la carpeta puede estar compartida entre los dos sistemas. Un acceso directo en la carpeta Inicio de Windows lo arranca al entrar en la sesión. El servicio de systemd ([0006](0006-el-launcher-como-servicio-de-systemd.md)) sigue siendo el arranque en Linux.
- **Un registro por sistema.** Cada sistema apunta `HOME_LAUNCHER_DATOS` a su propia carpeta de datos con su `proyectos.toml`. El código es el mismo; las rutas siguen siendo relativas a `Data` (`HOME_LAUNCHER_RAIZ`).

## Alternativas descartadas

- **Ficheros de PID para los proyectos sin puerto**: ya descartados en [0003](0003-el-puerto-como-fuente-de-verdad.md); no ven lo arrancado fuera de la Lanzadera ni sobreviven a un reinicio.
- **Proyecto sin puerto sin estado**: un interruptor que arranca pero nunca sabe si el proyecto corre ni puede pararlo.
- **`ss`/`ps`/`/proc` en Linux y `psutil` solo en Windows**: Linux no cambiaría, pero habría dos caminos que mantener y probar para lo mismo.
- **Terminar el árbol de procesos también en Linux**: un solo camino de parada, pero puede dejar vivo un proceso que se desligó de su padre y sigue en el grupo, que `killpg` sí alcanza.
- **Exigir siempre `cmd_detener` en Windows**: cada proyecto tendría que traer un script de parada aunque baste con terminar su proceso.
- **Tarea programada para el launcher**: puede reiniciarlo si se cae, pero es más configuración y menos visible que un acceso directo en Inicio.

## Consecuencias

- `psutil` entra en `requirements.txt`. Los tests que parsean la salida de `ps` y `ss` (`tests/test_ram.py`) y el que lee un `meminfo` de prueba (`tests/test_demo.py`) se rehacen sobre `psutil` simulado.
- Un `proceso` demasiado genérico (por ejemplo, `python`) haría que el proyecto pareciera activo con cualquier proceso que lo contenga: es un riesgo nuevo para [9 — Riesgos](../A1-Vision/9-riesgos.md), del mismo tipo que el del puerto ocupado por otro proceso.
- Todo lo que hoy trata la falta de `puerto` como fila de solo enlaces tiene que distinguir si hay `proceso`: estado, fila, buscador, filtros de estado, Local y RAM.
- Hay que actualizar `doc/A1-Vision/3-modelo-de-datos.md` (clave `proceso`), `doc/A1-Vision/4-casos-de-uso.md`, `doc/A1-Vision/9-riesgos.md` y el `README.md` (arranque en Windows).
- La parada en Windows y el arranque con `start.cmd` solo se pueden verificar en Windows; en Linux se prueban con `psutil` simulado.

## Estado

Propuesta — issue [#9](https://github.com/davidbp845/lanzadera/issues/9).

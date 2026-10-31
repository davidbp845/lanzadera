# 0018 — Lanzadera en macOS

## Contexto

La Lanzadera también tiene que funcionar en un Mac, con sus propios proyectos. No se trata de llevar allí los proyectos de otra máquina: el Mac clona el código del launcher y tiene su propio registro.

Desde [0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md), procesos, RAM, carpetas y puertos salen de `psutil`, y la parada sin `cmd_detener` es `SIGTERM` al grupo de procesos fuera de Windows. Casi todo eso vale en macOS sin cambios, salvo tres piezas:

- **Puertos.** En macOS, `psutil.net_connections()` exige root y lanza `AccessDenied`. `puertos_en_escucha()` lo captura y devuelve un diccionario vacío, así que ningún proyecto con puerto aparecería activo ([0003](0003-el-puerto-como-fuente-de-verdad.md)).
- **Arranque del launcher.** No hay systemd ([0006](0006-el-launcher-como-servicio-de-systemd.md)): el equivalente de un servicio de usuario es un LaunchAgent de `launchd`.
- **`stop.sh`.** Busca el proceso del launcher por su carpeta con `readlink -f /proc/$p/cwd`, y macOS no tiene `/proc`.

## Decisión

- **Puertos sin root.** `puertos_en_escucha()` intenta primero `psutil.net_connections("tcp")`. Si da `AccessDenied`, recorre los procesos con `psutil.process_iter()` y pide a cada uno sus conexiones (`Process.net_connections("tcp")`), que macOS sí entrega para los procesos del propio usuario. Los procesos que tampoco las entregan se saltan. La salida sigue siendo la de `puertos_de()`: puerto en escucha → PID. El cambio depende del error, no del sistema: en Linux y Windows sigue mandando la llamada global.
- **Parada.** macOS sigue el camino de Linux: `cmd` se lanza con `start_new_session=True` y, sin `cmd_detener`, se envía `SIGTERM` al grupo de procesos. No hace falta código nuevo.
- **El launcher como LaunchAgent.** `deploy/` lleva una plantilla de `.plist` para `~/Library/LaunchAgents/`, con:
  - `RunAtLoad`, para que arranque al iniciar sesión;
  - `KeepAlive` con `SuccessfulExit` en falso, el equivalente de `Restart=on-failure`;
  - `WorkingDirectory` en la carpeta del launcher;
  - `ProgramArguments` con `venv/bin/python -m streamlit run app.py`;
  - `HOME_LAUNCHER_DATOS` y `HOME_LAUNCHER_RAIZ` en `EnvironmentVariables`, porque un LaunchAgent no lee el entorno de la shell.

  Se instala con `launchctl bootstrap gui/$(id -u) <plist>`.
- **`stop.sh` portable.** La carpeta de cada proceso candidato sale de `psutil` con el Python del `venv/`, el mismo que usa el launcher, en lugar de `/proc`. Vale en Linux y en macOS.
- **Contenedor y datos propios por máquina.** El Mac tiene su propio contenedor local ([0001](0001-contenedor-local-con-los-datos.md)), con `lanzadera` como submódulo y su `datos/` (`proyectos.toml`, y `enlaces.csv` y `vps.toml` si se usan). Los registros de las dos máquinas no se comparten ni se sincronizan. Los cambios de código llegan a las dos máquinas por el repo público.
- **Arranque delegado en el proyecto**, como en [0002](0002-arranque-y-parada-delegados-en-cada-proyecto.md): un proyecto del Mac con agente propio de `launchd` lleva en `cmd`/`cmd_detener` sus `launchctl kickstart`/`launchctl bootout`, igual que los servicios de systemd llevan `systemctl --user start|stop`.

## Alternativas descartadas

- **Ejecutar el launcher como root** para que `net_connections()` funcione: el panel no tiene autenticación y arranca procesos; con root, cualquier `cmd` del registro correría como root.
- **`lsof -iTCP -sTCP:LISTEN` en un subproceso**: funciona sin root, pero vuelve a parsear la salida de una herramienta del sistema, que es lo que [0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md) quitó al pasar a `psutil`.
- **Recorrer siempre proceso a proceso, en los tres sistemas**: un solo camino, pero en Linux se dejaría de ver como activo un puerto de otro usuario, que hoy sale activo sin PID; y es más lento que la llamada global.
- **Elegir el camino por sistema (`sys.platform == "darwin"`)** en lugar de por el error: añade una rama por sistema donde basta con reaccionar a `AccessDenied`.
- **`start.command` con doble clic o como ítem de inicio de sesión**: abre una ventana de Terminal y no vuelve a arrancar el launcher si se cae, que es lo que `KeepAlive` da.
- **Una carpeta `datos-mac/` en el contenedor de otra máquina**, como `datos-windows/`: tiene sentido cuando los dos sistemas comparten disco; el Mac es otra máquina, con sus datos y su historial propios.

## Consecuencias

- En macOS, un puerto ocupado por un proceso de otro usuario no se ve: el proyecto aparece parado en lugar de activo sin RAM, como en Linux. Es una variante del riesgo «Choque de puertos» de [9 — Riesgos](../A1-Vision/9-riesgos.md): el proyecto no arrancaría y el panel no diría por qué.
- Recorrer los procesos uno a uno cuesta más que una sola llamada, y la Lanzadera mira los puertos en cada refresco. El coste se mide en el Mac; si se nota, se cachea en la sesión como el resto de lecturas del sistema.
- Con `launchd`, reiniciar el agente para el grupo de procesos del launcher. Los proyectos arrancados con `start_new_session=True` están en su propia sesión, así que, a diferencia de systemd ([0006](0006-el-launcher-como-servicio-de-systemd.md)), no deberían pararse con él. Se comprueba al instalarlo.
- Los tests de `puertos_en_escucha()` cubren el camino de respaldo con un `psutil` simulado que lanza `AccessDenied`. El LaunchAgent, la parada y la medición real solo se pueden verificar en un Mac.
- Hay que actualizar `README.md` (arranque en macOS), `doc/A1-Vision/2-entradas-y-salidas.md` (puertos sin root), `doc/A1-Vision/3-modelo-de-datos.md` (parada en macOS), `doc/A1-Vision/4-casos-de-uso.md` (usar la Lanzadera en macOS), `doc/A1-Vision/6-integraciones.md` (LaunchAgent) y `doc/A1-Vision/9-riesgos.md`.

## Estado

Propuesta (2026-10-31), sin issue de implementación todavía.

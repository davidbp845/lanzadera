# 2. Entradas y salidas

## Entradas

| Entrada | Dónde | Quién la cambia |
|---|---|---|
| Registro de proyectos | `datos/proyectos.toml` | A mano o con Claude, al dar de alta un proyecto (nivel B) |
| Enlaces | `datos/enlaces.csv` | `scripts/anadir_enlace.py` (lo llaman `/crear-enlace` y las automatizaciones de otras apps), o a mano |
| Servidores de la página VPS | `datos/vps.toml` | A mano o con Claude |
| Estado del VPS | `ssh <host> sh -s` con `scripts/estado_vps.sh` | El servidor |
| Estado de cada proyecto | Puertos TCP en `127.0.0.1` (`socket.connect_ex`); sin puerto, la línea de comando de sus procesos (`proceso`, con `psutil`) | Los propios proyectos al arrancar o parar |
| PID de quien escucha un puerto, procesos y su RAM | `psutil`, en Linux y en Windows ([ADR-0017](../A2-ADR/0017-lanzadera-en-windows-y-proyectos-sin-puerto.md)) | — |
| Commits por día (mapa de actividad) | `git log --all --format=%cs` en cada carpeta del registro y sus submódulos | Los propios proyectos |
| RAM total de la máquina | `psutil.virtual_memory()` | — |
| Idioma del panel | `HOME_LAUNCHER_IDIOMA` y el selector del lateral | El usuario |
| Lista de negocios y sus puertos | `HerukaLife/heruka-flow/scripts/dev_up.sh --listar` | heruka-flow |
| Interruptores del panel y botón Refrescar | Interacción del usuario | El usuario |

Con `HOME_LAUNCHER_DEMO=1`, todas estas entradas salen de `demo/` y no se consulta nada del sistema ([ADR-0010](../A2-ADR/0010-demo-publica-de-solo-lectura.md)).

Los ficheros de `datos/` se releen en cada recarga de la página (Streamlit reejecuta `app.py`): un cambio se ve al refrescar, sin reiniciar el servicio.

## Salidas

| Salida | Cómo |
|---|---|
| Arranque de un proyecto | `subprocess.Popen(cmd, cwd=ruta)` con salida a `/dev/null`, en sesión propia (`start_new_session=True`) en Linux y en grupo de procesos propio (`CREATE_NEW_PROCESS_GROUP`) en Windows |
| Parada de un proyecto | Su `cmd_detener` o, sin él, a quien escucha el puerto o a los procesos de su `proceso`: en Linux, `SIGTERM` a su grupo de procesos; en Windows, `terminate` del proceso y sus hijos y `kill` a los que sigan vivos |
| Arranque/parada de negocios | `dev_down.sh` y `dev_up.sh --skip-checks --negocios a,b` |
| Páginas del panel | Streamlit en `:8501` |

El panel no escribe en `datos/`: solo lo lee. Los cambios en `datos/` los hacen el usuario, Claude o, para añadir enlaces, quien llame a `scripts/anadir_enlace.py`; se versionan con commit en el contenedor, que el script no hace.

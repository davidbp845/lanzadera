# 6. Integraciones

## Proyectos hermanos

Para arrancar y parar, home solo conoce de cada proyecto lo que dice su fila del registro. Para los enlaces a GitHub de la Lanzadera lee además, sin escribir nada, el remoto git de su carpeta (o del primer submódulo) y la línea `Tablero` de su `CLAUDE.md`; si faltan, el proyecto sale sin enlace. El recuento de cada tablero se pide a la API de GitHub con `gh` (solo lectura), así que necesita `gh` con sesión para el usuario que ejecuta `home-streamlit`. La misma consulta lee el campo `Latido` del tablero, que escribe el plugin `dev` del método común mientras una sesión de Claude Code trabaja en un issue ([ADR-0016](../A2-ADR/0016-latido-del-issue-en-curso.md)); el launcher no lo escribe nunca. Para el mapa de actividad lee `git log` de su carpeta y de sus submódulos, también sin escribir. El contrato con cada uno es:

- un **puerto** fijo en su propia configuración (no se pasa desde home, salvo los Astro, que lo reciben con `--port`);
- un **comando de arranque** no interactivo, ejecutable desde su carpeta (p. ej. `dev_up.sh --skip-checks`, para que no se quede esperando un `read -p` con la salida en `/dev/null`);
- si matar a quien escucha el puerto no basta, un **comando de parada** propio.

Si un proyecto cambia su estructura (p. ej. pasa a contenedor + submódulo), se corrige su `ruta` en el registro; si cambia su forma de arrancar, se cambia su script, no home ([ADR-0002](../A2-ADR/0002-arranque-y-parada-delegados-en-cada-proyecto.md)).

## heruka-flow (filas de negocios de la Lanzadera)

- `scripts/dev_up.sh --listar`: una línea por negocio, `id<TAB>front<TAB>panel<TAB>api`.
- `scripts/dev_up.sh --skip-checks --negocios a,b`: arranca los elegidos.
- `scripts/dev_down.sh`: para todo el stack. Lo hace por patrón de comando, así que también para cualquier otro proyecto que use `npm run dev` o `astro dev`.

Ver [ADR-0005](../A2-ADR/0005-negocios-los-puertos-los-decide-heruka-flow.md).

## VPS (SSH)

- `ssh -o BatchMode=yes -o ConnectTimeout=5 <host> sh -s`, con `scripts/estado_vps.sh` por la entrada estándar; tiempo máximo, 15 s.
- `host` es un alias de `~/.ssh/config`. Tiene que entrar sin interacción desde `home-streamlit.service` (clave sin frase o agente accesible desde systemd de usuario); si no, la página muestra el error de ssh.
- La sección Contenedores sale solo si el servidor tiene `docker`, y necesita que el usuario SSH pueda usarlo (grupo `docker`); si no, muestra el error de permiso. Estar en el grupo `docker` equivale a ser root en el servidor: si no se quiere dar, la sección muestra el error y el resto de la página funciona igual.

Ver [ADR-0008](../A2-ADR/0008-pagina-vps-estado-por-ssh-bajo-demanda.md).

## Otras apps (alta de enlaces)

Una automatización de otro proyecto añade un enlace a la página Enlaces con:

```bash
python3 <ruta a lanzadera>/scripts/anadir_enlace.py "descripcion" "url" "etiqueta1;etiqueta2"
```

- Escribe en `enlaces.csv` de la carpeta de datos (`HOME_LAUNCHER_DATOS` o `../datos`), con el módulo `csv`; si el fichero no existe, lo crea con la cabecera.
- Código de salida `0` si añade la fila; `1` si la rechaza (la URL no empieza por `http://` o `https://`, o ya está en el CSV), con el motivo en la salida de error; `2` si no recibe tres argumentos.
- No hace commit: la fila queda sin commitear en el contenedor hasta que el usuario la revisa.
- Convención: añadir la etiqueta `Revisar` a los enlaces que entran por una automatización, para filtrarlos en la página Enlaces.

## systemd (usuario)

- home corre como `home-streamlit.service` (copia en `deploy/`), con `enable`: arranca al iniciar sesión.
- Un proyecto con servicio propio lleva en su fila `systemctl --user start|stop <servicio>`.

Ver [ADR-0006](../A2-ADR/0006-el-launcher-como-servicio-de-systemd.md).

## Windows (carpeta Inicio)

- En Windows no hay servicio: un acceso directo a `start.cmd` en la carpeta Inicio (`shell:startup`) arranca el launcher al entrar en la sesión. `start.cmd` usa `venv-windows/`, porque `venv/` es el de Linux y la carpeta puede estar compartida entre los dos sistemas.
- Los proyectos de Windows llevan en `cmd` su propio script o ejecutable (`.cmd`, `.ps1`, el intérprete con su script), nunca un `start.sh`.

Ver [ADR-0017](../A2-ADR/0017-lanzadera-en-windows-y-proyectos-sin-puerto.md).

## Terminal

`/crear-atajo` mantiene en `~/.bashrc` una función por proyecto de `Data/` (`_proyecto Grupo/carpeta`), que entra en la carpeta y abre `claude`. home es la carpeta del contenedor (`Apps/home`).

# 0006 — El launcher como servicio de usuario de systemd

## Contexto

home tiene que estar disponible siempre, sin abrir una terminal. Algunos proyectos (namesyncia, emailmanage) también corren como servicios.

## Decisión

- `home-streamlit.service` (copia en `deploy/`), servicio de usuario con `enable`, `Restart=on-failure` y `RequiresMountsFor` del disco `Data`.
- Los proyectos con servicio propio se arrancan y paran desde home con `systemctl --user start|stop`: con su `start.sh` habría dos procesos peleando por el puerto.
- `start.sh`/`stop.sh` en el submódulo, solo para desarrollo.

## Alternativas descartadas

- **Arranque a mano o en `.bashrc`**: depende de abrir una terminal.

## Consecuencias

- Los proyectos que home arranca con `Popen` quedan en el grupo de control del servicio: **reiniciar `home-streamlit` los para** (con `KillMode` por defecto). Los que tienen servicio propio no se ven afectados.
- Cambiar la ruta del código (como en el ADR-0001) obliga a actualizar el servicio instalado y hacer `daemon-reload`.

## Estado

Aceptada (fecha sin documentar). Ampliada por [0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md).

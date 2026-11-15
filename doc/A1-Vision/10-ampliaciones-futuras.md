# 10. Ampliaciones futuras

Ideas sin compromiso; cada una, si madura, es un issue en Backlog.

- **Ver el log** de un proyecto que no arranca (al menos las últimas líneas), en vez de descartar su salida.
- **Puerto ocupado por otro**: avisar si quien escucha el puerto no es un proceso de la carpeta del proyecto.
- **Validar el registro al cargar** (puertos repetidos, rutas que no existen) y mostrarlo en el panel.
- **Recompilar la web al arrancar heruka-flow**: una casilla junto a la selección de negocios que pase `--rebuild-front` a `dev_up.sh`. Sin ella, cada negocio sirve lo último que hay en `frontend/dist-<negocio>`, y un cambio en `business.yaml`, en el vault o en el frontend no se ve hasta recompilar desde la terminal.
- **Separar `app.py`** en procesos (arranque/parada/puertos) y páginas si crece ([ADR-0007](../A2-ADR/0007-estructura-plana-sin-hexagonal.md)).

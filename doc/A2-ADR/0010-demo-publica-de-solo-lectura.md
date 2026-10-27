# 0010 — Demo pública de solo lectura con datos de ejemplo

## Contexto

Se quiere compartir la Lanzadera con la comunidad Streamlit ([#10](https://github.com/davidbp845/home/issues/10)), y lo que más ayuda allí es un enlace que se pueda abrir y probar, no solo capturas. Pero la visión deja fuera el acceso remoto ([7 — Fuera de alcance](../A1-Vision/7-fuera-de-alcance.md)): el panel escucha solo en `127.0.0.1` y no tiene autenticación porque arranca y para procesos ([9 — Riesgos](../A1-Vision/9-riesgos.md)). Además, todo lo que muestra sale de esta máquina: `datos/` reales ([ADR-0001](0001-contenedor-local-con-los-datos.md)), puertos y procesos locales, `gh` y SSH al VPS ([ADR-0008](0008-pagina-vps-estado-por-ssh-bajo-demanda.md)).

## Decisión

- **Dos despliegues del mismo código**. El de uso sigue igual: `home-streamlit.service` en `127.0.0.1:8501`, sin autenticación ([ADR-0006](0006-el-launcher-como-servicio-de-systemd.md)). El de demo se publica en Streamlit Community Cloud y es el único accesible desde fuera.
- **Modo demo por variable de entorno** (`HOME_LAUNCHER_DEMO=1`), leído en `config/paths.py` junto a `HOME_LAUNCHER_DATOS`. No añade claves a `datos/proyectos.toml`.
- **Solo lectura de verdad**: en modo demo no se ejecuta nada del sistema. Arrancar y Detener se muestran deshabilitados, y el estado de los puertos, la RAM (`ps`/`ss`), los recuentos de GitHub (`gh`), la actividad (`git log`) y el estado del VPS (SSH) salen de datos de ejemplo, no de llamadas reales. El corte va en cada función que consulta el sistema, no solo en los botones, para que un fallo de la interfaz no pueda lanzar un proceso.
- **Datos de ejemplo versionados en el submódulo** (`demo/`): proyectos, negocios, enlaces y salidas del VPS ficticios, con el mismo formato que `datos/`, escritos en inglés. Nada de `datos/` entra en la demo.
- **Interfaz en dos idiomas**: los textos visibles del panel salen de un diccionario por idioma, elegido con `HOME_LAUNCHER_IDIOMA` (`es` por defecto, `en` en la demo). Sin gettext ni babel: es una sola app con dos idiomas. Código, comentarios y `doc/` siguen en español; el `README.md` va en inglés.

## Alternativas descartadas

- **Solo GIF y capturas en el README**: no hace falta desplegar nada, pero en la galería y en el foro se valora poder abrir la app. El GIF se hace igualmente, para el README.
- **Exponer el launcher real con autenticación**: daría acceso desde fuera a arrancar y parar procesos de esta máquina y a datos personales; es justo lo que la visión deja fuera.
- **Una app de demo aparte**, copiando las páginas: duplicaría el código y se desfasaría con cada cambio del panel.
- **Pasar toda la interfaz a inglés**: el uso diario es en español.
- **Demo en español**: la comunidad Streamlit lee en inglés, y la demo es lo primero que ve.
- **Modo demo solo deshabilitando los botones**: las consultas de puertos, `ps`, `gh` y SSH seguirían corriendo en el servidor de Community Cloud, fallando o enseñando datos de ese servidor.

## Consecuencias

- La visión pasa a contemplar la demo: al implementar se actualizan [7 — Fuera de alcance](../A1-Vision/7-fuera-de-alcance.md) (el acceso remoto sigue fuera para el launcher real; la demo es la excepción), [9 — Riesgos](../A1-Vision/9-riesgos.md) (que el modo demo deje pasar una llamada real), [5 — Panel](../A1-Vision/5-panel-streamlit.md) y el `README.md`.
- Cada función que consulta el sistema necesita su variante de ejemplo, y cada página nueva o consulta nueva tiene que contemplar el modo demo. Los tests comprueban con `AppTest` las páginas en modo demo y que en ese modo no se llama a `subprocess` ni a `socket`.
- Cada texto nuevo del panel se añade en los dos idiomas; un test comprueba que los dos diccionarios tienen las mismas claves.
- `.streamlit/config.toml` mantiene `address = "127.0.0.1"` para el uso local; hay que comprobar que Community Cloud lo ignora o darle allí su propia configuración.
- Publicar en Community Cloud pide un repo accesible desde allí: si se hace público `davidbp845/home` o se crea uno limpio es una decisión aparte de #10, igual que revisar que el código y la documentación no contengan datos personales.
- Los negocios de heruka-flow aparecen en la demo con nombres ficticios.

## Estado

Aceptada (2026-10-27). Implementación: [#11](https://github.com/davidbp845/home/issues/11).

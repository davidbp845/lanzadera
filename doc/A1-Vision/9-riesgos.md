# 9. Riesgos

| Riesgo | Consecuencia | Mitigación |
|---|---|---|
| Reiniciar `home-streamlit` | systemd para todo su grupo de control: los proyectos arrancados desde el launcher (sin servicio propio) se paran con él | Reiniciar cuando no haya nada arrancado, o volver a arrancarlos; documentado en `deploy/` |
| Un proyecto hermano cambia de estructura o de script | El interruptor falla en silencio (la salida va a `/dev/null`) | Revisar primero el `start.sh` del proyecto; corregir su `ruta` en el registro |
| Choque de puertos | Un proyecto parece activo porque otro ocupa su puerto, o no arranca | Revisar los puertos del registro antes de asignar uno |
| Un `proceso` demasiado genérico | Un proyecto sin puerto parece activo con cualquier proceso que lleve ese texto, y pararlo termina ese proceso | Un texto que solo lleve su proceso: el nombre de su script, no el del intérprete |
| Matar por puerto a un proceso ajeno | Se para algo que no era del proyecto (p. ej. otro `langgraph dev`) | `cmd_detener` propio cuando el puerto no identifica bien al proceso |
| Arranques lentos | Verde antes de tiempo, o vuelta a "parado" por timeout | Esperar a todos los puertos de `enlaces`; `intentos_espera_inicio` medido en logs |
| Error de formato en `datos/proyectos.toml` | La página no carga | `tests/test_proyectos.py` valida el registro real si existe |
| Exponer el panel a la red | Sin autenticación, cualquiera podría arrancar o parar proyectos | `server.address = "127.0.0.1"` en `.streamlit/config.toml`; no quitarlo |
| Que el modo demo deje pasar una llamada real | La demo pública ejecutaría algo en su servidor o enseñaría datos de él | Corte en cada función que consulta el sistema, no solo en los botones; `tests/test_demo.py` abre las cuatro páginas en demo con `subprocess`, `socket` y la lectura de procesos de `psutil` prohibidos |
| `dev_down.sh` de heruka-flow para por patrón (`npm run dev`, `astro dev`) | Arrancar, parar o cambiar negocios para también otros proyectos con `npm run dev` | Volver a arrancarlos después. Acotar el patrón es cambio de heruka-flow |
| Comandos del registro | El registro ejecuta lo que diga: es tan sensible como un script | Solo lo editan el usuario o Claude, y va con commit |

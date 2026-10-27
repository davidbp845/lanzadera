# 7. Explícitamente fuera de alcance

- **Ver logs** de los proyectos: cada uno escribe los suyos; home descarta la salida de lo que arranca.
- **Gestionar dependencias o builds** de los proyectos hermanos (instalar, migrar, compilar).
- **Acceso remoto** al launcher: escucha solo en `127.0.0.1` (`.streamlit/config.toml`) y no hay autenticación. Lo único accesible desde fuera es la demo pública, que no ejecuta nada y solo enseña datos de ejemplo ([ADR-0010](../A2-ADR/0010-demo-publica-de-solo-lectura.md)).
- **Arrancar proyectos al iniciar sesión**: lo hace systemd para quien lo necesite, no home.
- **Supervisar** (reiniciar lo que se cae, alertas). El semáforo refleja el estado al cargar la página; no hay vigilancia continua. La página VPS tampoco: consulta al entrar y al pulsar Refrescar, nunca sola.
- **Actuar sobre el VPS** (reiniciar servicios, desplegar): la página VPS solo lee.
- **Editar enlaces o proyectos desde el panel**: se editan los ficheros de `datos/` (a mano o con Claude) y se versionan.
- **Lógica de negocio de heruka-flow**: home solo llama a sus scripts.

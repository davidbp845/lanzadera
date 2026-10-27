# 1. Problema que resuelve

## Objetivo

Tener **un único sitio** (http://localhost:8501) desde el que ver, arrancar, parar y abrir todas las apps locales de `Data/` (Apps, HerukaLife, Otros), a mano los enlaces que se usan a diario, y un vistazo al estado del VPS.

## Situación

- Hay más de una decena de proyectos hermanos, cada uno con su puerto y su forma de arrancar: `./start.sh`, `scripts/dev_up.sh`, `npm run dev`, Docker Compose, servicios de systemd.
- Algunos levantan varios procesos (Heruka Life: backend, frontend y panel) y tardan decenas de segundos en estar listos.
- Sin el launcher, arrancar algo es recordar la carpeta, el comando, el puerto y si hay que parar otra cosa antes; y parar algo arrancado en segundo plano es buscar su PID.
- Los enlaces de trabajo (consolas de proveedores, documentación, paneles) están dispersos por marcadores de varios navegadores.

## Qué hace home

- **Lanzadera**: una fila por proyecto con su puerto, un semáforo (🟢 activo / ⚪ parado) y un interruptor que lo arranca o lo para. Cuando está activo, enlaces a cada uno de sus servicios; siempre, a su repositorio y su tablero de GitHub si los tiene, con el número de issues en cada estado del tablero. Buscador y filtros por carpeta y estado. En la misma tabla, los negocios multi-tenant de heruka-flow, que se arrancan juntos sobre un único backend. Encima, gráficos de issues abiertos por estado y de actividad de commits.
- **Enlaces**: tabla buscable y filtrable por etiquetas.
- **VPS**: estado del servidor (carga, memoria, disco, servicios con fallo, procesos, contenedores) leído por SSH al entrar y al pulsar Refrescar, con medidores de memoria, disco y carga.

## Principios

1. **Cada proyecto sabe arrancarse.** home no reconstruye comandos de arranque: delega en el script o servicio del propio proyecto ([ADR-0002](../A2-ADR/0002-arranque-y-parada-delegados-en-cada-proyecto.md)).
2. **La realidad manda.** Un proyecto está activo si su puerto responde, lo haya arrancado home o no ([ADR-0003](../A2-ADR/0003-el-puerto-como-fuente-de-verdad.md)).
3. **Datos fuera del código.** Qué proyectos hay y qué enlaces se muestran son datos del contenedor (`datos/`), no constantes de `app.py` ([ADR-0001](../A2-ADR/0001-contenedor-local-con-los-datos.md), [ADR-0004](../A2-ADR/0004-registro-de-proyectos-como-dato.md)).
4. **Solo local.** Escucha solo en `127.0.0.1`. Lo único que sale del equipo es la consulta SSH de solo lectura de la página VPS ([ADR-0008](../A2-ADR/0008-pagina-vps-estado-por-ssh-bajo-demanda.md)). La demo pública es otro despliegue, de solo lectura y con datos de ejemplo ([ADR-0010](../A2-ADR/0010-demo-publica-de-solo-lectura.md)).

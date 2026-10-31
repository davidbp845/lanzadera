# 0019 — Perfil de usuario final

## Contexto

La Lanzadera sirve a dos tipos de persona ([0018](0018-lanzadera-en-macos.md)): quien desarrolla con el método común y tableros de GitHub Projects, y quien solo usa las aplicaciones. Los dos arrancan y paran aplicaciones en su propia máquina y abren sus enlaces. Solo quien desarrolla necesita lo que gira alrededor del código:

- el gráfico de issues abiertos por estado, el de actividad de commits y las píldoras de orden por estado;
- la columna GitHub (repositorio, tablero y pastillas) y el botón «Actualizar tableros»;
- las páginas VPS ([0008](0008-pagina-vps-estado-por-ssh-bajo-demanda.md)) y Local.

Todo eso ya funciona sin GitHub: sin `## Método` en un `CLAUDE.md` o sin `gh`, sale `—` o no sale. Aun así, a quien solo usa las aplicaciones le llena la pantalla de huecos que no le dicen nada.

La parte difícil, arrancar y parar en los tres sistemas y saber el estado por puerto o por proceso ([0003](0003-el-puerto-como-fuente-de-verdad.md), [0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md), [0018](0018-lanzadera-en-macos.md)), la necesitan las dos.

## Decisión

- **Una sola aplicación con dos perfiles**, elegidos con la variable de entorno `HOME_LAUNCHER_PERFIL`: `desarrollo` (el valor por defecto, el comportamiento actual) o `usuario`. Se lee en `config/paths.py`, como `HOME_LAUNCHER_DEMO` ([0010](0010-demo-publica-de-solo-lectura.md)).
- **Perfil `usuario`:**
  - páginas Lanzadera y Enlaces;
  - en Lanzadera, el buscador, las píldoras de carpeta, tipo y estado, y la tabla con proyecto, puerto, estado, enlaces e interruptor.
- **Lo que el perfil `usuario` no muestra:** los gráficos, las píldoras de orden, «Actualizar tableros», la columna GitHub y las páginas VPS y Local.
- **Lo que el perfil `usuario` no ejecuta:** no llama a `gh` ni a `git log`, así que no necesita ninguno de los dos instalado.
- **El perfil decide qué se ve, no cómo funciona:** el registro (`datos/proyectos.toml`), el arranque, la parada y el estado son los mismos en los dos perfiles.
- **La demo pública sigue con el perfil `desarrollo`**, porque enseña la aplicación completa.

## Alternativas descartadas

- **Dos aplicaciones distintas**: el arranque, la parada y el estado en tres sistemas se mantendrían dos veces, o habría que sacarlos a una librería común solo para esto.
- **Deducir el perfil de si hay `gh` o un tablero**: una persona que desarrolla sin sesión en `gh`, o con la red caída, perdería la mitad del panel sin haberlo pedido.
- **Una clave en `datos/proyectos.toml`**: el registro describe los proyectos, no la instalación, y una clave nueva en el registro pide su propio cambio del modelo de datos.
- **Un selector de perfil en el lateral**: no hay nada que proteger, pero el usuario final vería opciones que nunca usa, y quien desarrolla no lo cambiaría nunca.

## Consecuencias

- Quien solo usa las aplicaciones no necesita ni `gh`, ni el método común, ni una cuenta de GitHub. Le basta Python, el `venv` y su `datos/`.
- `app.py` tiene que preguntar por el perfil en cada pieza de desarrollo. Si las ramas se multiplican, se agrupan en una función por pieza para que el perfil se mire una vez.
- Las páginas de los dos perfiles se comprueban con `AppTest`. La verificación de `## Método` añade la Lanzadera y Enlaces con `HOME_LAUNCHER_PERFIL=usuario`.
- Hay que actualizar `doc/A1-Vision/5-panel-streamlit.md` (qué ve cada perfil), `doc/A1-Vision/4-casos-de-uso.md`, `doc/A1-Vision/6-integraciones.md` (sin `gh` en el perfil usuario) y el `README.md` (variables de entorno y cómo instalarla solo para usarla).

## Estado

Propuesta (2026-10-31), sin issue de implementación todavía.

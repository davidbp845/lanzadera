# C3 — Diseño UX/UI

Nivel C de la [metodología](../A0-Metodologia/metodologia-de-diseno-y-desarrollo.md). Solo si el issue cambia lo que se ve en el panel.

- **Columna**: Ready
- **Índice del documento**: página(s) afectadas · estado antes/después · qué acciones arrancan o paran procesos

## Estado actual del panel

Descrito en [5 — Panel Streamlit](../A1-Vision/5-panel-streamlit.md). Pendiente: capturas de referencia de las páginas (Lanzadera, Enlaces, VPS, Local), guardadas aquí como `NN Página — estado.png`.

Tema: claro, color primario `#F63366`, barra de herramientas automática (`.streamlit/config.toml`): completa en localhost, mínima en la demo pública. Las etiquetas de Enlaces usan la paleta categórica validada de la skill dataviz, en orden fijo.

Tablero: [tablero (proyecto GitHub #9)](https://github.com/users/davidbp845/projects/9)

## Mockups

| Issue | Página | Estados |
|---|---|---|
| [#1](https://github.com/davidbp845/home/issues/1) · [ADR-0008](../A2-ADR/0008-pagina-vps-estado-por-ssh-bajo-demanda.md) | VPS | [conectado](mockups/01%20VPS%20—%20conectado.png) · [sin conexión, con datos antiguos](mockups/02%20VPS%20—%20sin%20conexión.png) · [sin `datos/vps.toml`](mockups/03%20VPS%20—%20sin%20configurar.png) |
| [#11](https://github.com/davidbp845/home/issues/11) · [ADR-0010](../A2-ADR/0010-demo-publica-de-solo-lectura.md) | Demo en inglés: Lanzadera, Enlaces, VPS, Local | [Lanzadera](mockups/04%20Demo%20—%20Lanzadera.png) · [Enlaces](mockups/05%20Demo%20—%20Enlaces.png) · [VPS](mockups/06%20Demo%20—%20VPS.png) · [Local](mockups/07%20Demo%20—%20Local.png) |

Cada PNG tiene al lado su HTML estático (`mockups/vps-*.html`, `mockups/demo-*.html`), para retocarlo y volver a capturarlo. Los datos que aparecen son de ejemplo.

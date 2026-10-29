# 0015 — Tipo de aplicación en el registro y píldoras por tipo

## Contexto

La Lanzadera filtra por carpeta raíz (`Apps`, `HerukaLife`…), por estado y, con la píldora **Negocios**, por las filas de heruka-flow ([ADR-0009](0009-negocios-como-filas-de-la-lanzadera.md)). No hay forma de ver juntas las apps de un mismo framework (Streamlit, Astro, Wagtail), que es como se piensa en ellas al mantenerlas: actualizar una dependencia, repasar un patrón común o arrancar las de un tipo.

El registro no sabe de qué tipo es cada proyecto. Deducirlo de la carpeta no es fiable: `requirements.txt` puede estar en un subproyecto (Planes, Conocimiento), una misma carpeta sirve un frontend Astro y un panel Streamlit (heruka-flow), y otros arrancan con Docker o LangGraph. Una clave nueva del registro es código y lleva ADR ([0004](0004-registro-de-proyectos-como-dato.md)).

La píldora **Negocios** de ADR-0009 ya hace lo que haría un tipo "heruka-flow": deja solo las filas de negocios multi-tenant (o la fila `[negocios.single]`). Tener las dos sería redundante.

## Decisión

- **Clave `tipo` opcional en `[[proyecto]]`**: texto libre con el framework principal de la app (`"Streamlit"`, `"Astro"`, `"Wagtail"`). Un solo valor por proyecto: el del servicio que da el puerto principal. Sin `tipo`, la fila no tiene tipo.
- **Las filas de negocios son tipo `heruka-flow`**, fijado en código para "Todos los negocios", cada negocio y `[negocios.single]`; no se escribe en el registro. Proyectos de la carpeta de heruka-flow que no son negocios (p. ej. una landing Astro o la consola de chat) llevan su propio `tipo`, o ninguno.
- **Píldoras de tipo**: una por cada valor presente en las filas, en orden alfabético, en el mismo grupo que las de carpeta y estado, detrás de las carpetas. Llevan la paleta de Enlaces por posición, como las de carpeta. El valor se muestra tal cual, sin traducir.
- **La píldora `heruka-flow` sustituye a Negocios**: misma función, con el nombre del stack. Sale solo si el registro tiene `[negocios]`.
- **Combinación**: los tipos se combinan entre sí con OR; tipos, carpetas, estados y buscador, con AND. Con un tipo activo, las filas sin tipo quedan fuera.
- Matiza [ADR-0009](0009-negocios-como-filas-de-la-lanzadera.md): la píldora Negocios queda superada por esta; el resto de esa decisión sigue igual.

## Alternativas descartadas

- **Detectar el tipo leyendo la carpeta** (`requirements.txt`, `package.json`): falla en los proyectos con el código en un subdirectorio o con varios servicios, añade lecturas de disco en cada rerun y no da un valor estable para la píldora.
- **Lista cerrada de tipos en el código**: obliga a tocar código para un framework nuevo, cuando dar de alta un proyecto es un dato. El texto libre genera las píldoras igual que las carpetas.
- **Varios tipos por proyecto** (`tipos = [...]`): Email Generator es Django y Wagtail, y Heruka Life Streamlit y Astro, pero la píldora busca "las apps de X", y el framework del puerto principal basta. Se puede ampliar si hace falta.
- **Mantener Negocios junto a `heruka-flow`**: dos píldoras que dejan las mismas filas.

## Consecuencias

- Se vuelve fácil ver y arrancar las apps de un mismo framework. Clasificar un proyecto es añadir una línea al registro.
- El grupo de píldoras crece: con tres carpetas y cuatro tipos son siete colores, y la paleta tiene ocho. Más valores distintos reciclarían colores; si llega, se separan los tipos en su propio grupo.
- Un `tipo` mal escrito (`"streamlit"` frente a `"Streamlit"`) crea una píldora aparte: el valor no se normaliza, porque es lo que se muestra.
- La demo pierde la píldora traducida "Businesses": sale `heruka-flow`, que es un nombre propio. Su `demo/proyectos.toml` gana `tipo` en sus filas para enseñar las píldoras.
- Docs a actualizar al implementar: [3 — Modelo de datos](../A1-Vision/3-modelo-de-datos.md) (clave `tipo`) y [5 — Panel](../A1-Vision/5-panel-streamlit.md) (píldoras de tipo, sin Negocios). Tests de `config/proyectos.py` y del filtro de la Lanzadera.

## Estado

Aceptada (2026-10-29) — issue [#8](https://github.com/davidbp845/lanzadera/issues/8).

# 0009 — Negocios como filas de la Lanzadera

## Contexto

[ADR-0005](0005-negocios-los-puertos-los-decide-heruka-flow.md) dio a los negocios de heruka-flow una página propia, separada de la de proyectos, cuando esa página era una lista sin filtros. La Lanzadera es ahora una tabla filtrable: buscador mientras se escribe, píldoras por carpeta y estado, y contador. Tener los negocios en otra página obliga a cambiar de menú para ver qué hay activo en la máquina, y a mantener dos listas con el mismo formato de fila.

Lo que hace la página Negocios no cambia: la lista y los puertos los da `dev_up.sh --listar`, el backend (`:8000`) es compartido y cambiar la selección relanza el stack entero. Sin `NEGOCIOS_MULTITENANT` se muestra la fila única `[negocios.single]` (Heruka Life).

## Decisión

- **Una sola página**: los negocios pasan a ser filas de la tabla de la Lanzadera y la opción Negocios sale del menú, que queda con Lanzadera, Enlaces, VPS y Local.
- **Las mismas filas que hoy**:
  - con multi-tenant, una fila "Todos los negocios" y una por negocio de `--listar`, con su puerto de panel y, si está activo, enlaces a Frontend, Panel y API;
  - sin multi-tenant, la fila `[negocios.single]`, igual que un proyecto con `enlaces`.
- **Mismos interruptores**: cada `st.toggle` llama a `iniciar_negocios()` con la nueva selección. Arrancar o parar uno sigue relanzando el stack entero y el de "Todos" arranca o para todos ([ADR-0005](0005-negocios-los-puertos-los-decide-heruka-flow.md)).
- **Filtros**:
  - las filas de negocios cuentan como carpeta `HerukaLife` y entran en el buscador por nombre e id;
  - una píldora más, **Negocios**, deja ver solo esas filas;
  - el estado (activo, parado) se calcula por sus puertos, como ahora.
- **GitHub**: repositorio y tablero de heruka-flow, con `github.py` sobre su carpeta (`[negocios] ruta`).
- **`--listar` cacheado**: el buscador relanza la página tras cada pausa al escribir, y `--listar` puede tardar (hasta 10 s de límite). La lista se guarda con `st.cache_data` (60 s) y se invalida al arrancar o parar negocios.

## Alternativas descartadas

- **Seguir con dos páginas**: cada página de por sí funciona, pero no hay una vista única de lo que corre en la máquina, y el filtro de la Lanzadera no alcanza a los negocios.
- **Un `[[proyecto]]` por negocio en el registro**: ya descartada en ADR-0005; duplicaría en home la configuración de heruka-flow y no reflejaría el backend compartido.
- **Un desplegable de negocios dentro de la Lanzadera**: esconde filas que el buscador y el contador tendrían que tratar aparte.
- **Llamar a `--listar` en cada rerun**: con el buscador en vivo, cada pausa al escribir podría costar segundos.

## Consecuencias

- Un negocio arrancado o parado desde fuera del panel puede tardar hasta 60 s en reflejarse en la lista. El semáforo no se retrasa, porque sigue saliendo del puerto ([ADR-0003](0003-el-puerto-como-fuente-de-verdad.md)). Lo que se retrasa es la aparición de un negocio nuevo en `--listar`.
- La verificación de `## Método` (`CLAUDE.md`) y la de los tests dejan de mencionar la página Negocios y pasan a cubrir sus filas dentro de Lanzadera.
- Docs a actualizar al implementar:
  - [5 — Panel](../A1-Vision/5-panel-streamlit.md), con cuatro páginas y la sección Negocios dentro de Lanzadera;
  - [1 — Problema](../A1-Vision/1-problema-que-resuelve.md);
  - [4 — Casos de uso](../A1-Vision/4-casos-de-uso.md);
  - [6 — Integraciones](../A1-Vision/6-integraciones.md), donde "página Negocios" pasa a "filas de negocios";
  - el README.
- Los demás proyectos de la carpeta de heruka-flow (p. ej. Heruka Consola) siguen siendo `[[proyecto]]` aparte. La píldora Negocios distingue las filas de negocios de ellos.
- La página Local ([#5](https://github.com/davidbp845/home/issues/5)) no cambia por esto.

## Estado

Aceptada (2026-10-27). Implementación: [#7](https://github.com/davidbp845/home/issues/7).

# 0012 — El repo público `lanzadera` sustituye a `home` como código del launcher

## Contexto

Para compartir la Lanzadera ([0010](0010-demo-publica-de-solo-lectura.md), [0011](0011-licencia-mit.md)) se creó `davidbp845/lanzadera`, público, como copia aparte del submódulo `davidbp845/home` (privado) de [0001](0001-contenedor-local-con-los-datos.md). La demo de https://lanzadera.streamlit.app se despliega desde `lanzadera`.

Las dos copias tienen el mismo código, salvo la URL del repo y el `.service` de ejemplo. Lo que las separa es la documentación: `home` guarda además documentación privada (fichas B1 de los proyectos hermanos, mapa de puertos, permisos del VPS, lecciones aprendidas completas) y un historial con datos personales. Mantener las dos al día obliga a copiar cada cambio a mano, y se desincronizan sin avisar.

## Decisión

- **`lanzadera` es el código y la documentación del launcher.** Sustituye a `home` como submódulo del contenedor de [0001](0001-contenedor-local-con-los-datos.md); el resto de esa decisión (contenedor solo local con `datos/`, sin remoto) sigue igual.
- **`davidbp845/home` se archiva en GitHub**, privado y en solo lectura, como histórico del launcher: sus 52 commits, sus issues, sus ADR con los enlaces a esos issues y la documentación privada, que se queda allí congelada.
- Los issues abiertos de `home` se vuelven a crear en `lanzadera`, sin datos personales en el texto: GitHub no transfiere issues de un repo privado a uno público.
- `home` se archiva al final, cuando el contenedor, el servicio y el registro ya usan `lanzadera` y no queda nada sin subir.

## Alternativas descartadas

- **`home` manda y `lanzadera` es un espejo**: cada cambio se copiaría y saneado a mano, que es justo el problema de tener dos copias.
- **Hacer público `home`**: su historial tiene rutas, nombres de negocios y datos de los proyectos hermanos; habría que reescribirlo y aun así quedaría la documentación privada.
- **Mover la documentación privada al contenedor**: seguiría editable, pero el contenedor no tiene remoto y quedaría solo en este disco. Archivada en `home` tiene copia en GitHub.

## Consecuencias

- Un solo repo que mantener. Cada push a `main` de `lanzadera` vuelve a desplegar la demo.
- Los issues y commits son públicos. Lo que la verificación permitía en un issue privado (nombres de proyectos hermanos, rutas y puertos del registro) se revisa antes de escribirlo.
- La documentación privada archivada deja de ser editable. El mapa de puertos y las fichas B1, que siguen cambiando, se copian a `doc-local/` del contenedor y se editan allí, solo en este disco como `datos/`.
- El historial anterior a `lanzadera` solo está en `home` archivado. Los punteros al submódulo de commits antiguos del contenedor siguen resolviéndose mientras `home` exista.
- Cambian de ruta `home-streamlit.service` ([0006](0006-el-launcher-como-servicio-de-systemd.md)), la fila de la propia Lanzadera en `datos/proyectos.toml`, `.gitmodules` y la sección `## Método` del `CLAUDE.md`. Al reiniciar el servicio para aplicarlo se paran los proyectos arrancados desde la Lanzadera.
- Archivar se puede deshacer desde los ajustes del repo en GitHub.

## Estado

Propuesta (2026-10-27) — issue [#1](https://github.com/davidbp845/lanzadera/issues/1).

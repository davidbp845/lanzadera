# 0011 — Licencia MIT

## Contexto

La Lanzadera se va a compartir en público, en el foro y la galería de Streamlit ([#10](https://github.com/davidbp845/home/issues/10)), y el repo no tiene licencia. Sin licencia, nadie puede usar, copiar ni modificar el código, aunque sea visible.

El autor no vende el código. Vende servicios sobre las apps: personalizarlas, instalarlas y formar a los clientes como cuota inicial, más una cuota recurrente opcional de soporte y actualización automática. Como único autor, puede vender esos servicios sobre su propio código con cualquier licencia, porque la licencia obliga a los demás, no a él.

## Decisión

- **MIT** para todo el repo: fichero `LICENSE` en la raíz y una sección *License* en el `README.md`.
- El titular del copyright es el autor. Lo que diferencia los servicios es el nombre «Lanzadera» y la experiencia del autor, no la licencia: el README lo dice en una línea.
- La licencia cubre solo este repo. Cada proyecto hermano decide la suya en su propio repo.

## Alternativas descartadas

- **AGPL-3.0**: obliga a publicar los cambios de quien sirva la app en red, pero no impide que otros vendan los mismos servicios, y algunas empresas evitan el código AGPL. Para un launcher local, la protección que añade apenas cuenta.
- **PolyForm Noncommercial 1.0.0**: reserva el uso comercial al autor, que podría vender licencias. No es una licencia de código abierto, encaja peor en la galería de Streamlit, y el negocio del autor no está en vender licencias del launcher.
- **Sin licencia**: el código no se podría usar legalmente, lo que contradice el objetivo de compartirlo.

## Consecuencias

- Cualquiera puede usar, modificar y vender servicios con la Lanzadera, incluida la competencia, siempre que conserve el aviso de copyright.
- Las dependencias (Streamlit, Apache-2.0; pandas y Altair, BSD) son compatibles con MIT y no imponen nada más.
- Los contratos con clientes (soporte, actualizaciones) se rigen por el contrato de servicios, no por la licencia.
- Si un proyecto hermano se publica más adelante, su licencia se decide aparte.

## Estado

Aceptada (2026-10-27). Implementación: [#10](https://github.com/davidbp845/home/issues/10).

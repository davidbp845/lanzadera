# B3 — Puesta en marcha de un proyecto en el launcher

Nivel B de la [metodología](../A0-Metodologia/metodologia-de-diseno-y-desarrollo.md). Checklist única para cualquier alta, estándar o no.

1. [ ] Puerto libre (que no lo use ninguna fila del registro); fijado en la configuración del propio proyecto.
2. [ ] El arranque funciona desde la carpeta del proyecto, sin terminal interactiva (`cmd < /dev/null > /dev/null`).
3. [ ] Fila en `datos/proyectos.toml`, con comentario si tiene claves no triviales. `./venv/bin/pytest` en verde (valida el registro real).
4. [ ] En el panel: el interruptor arranca, el semáforo se pone verde solo cuando responde el último servicio y los enlaces abren.
5. [ ] El interruptor para, el semáforo vuelve a ⚪ y no quedan procesos (`ss -ltnp`, `/uso-ram`).
6. [ ] Si se arrancó fuera de home (terminal o systemd), el semáforo también lo ve y el interruptor lo para.
7. [ ] Atajo de terminal con `/crear-atajo`, si no lo tiene.
8. [ ] Commit en el contenedor: `Launcher: añade <Nombre> (puerto N[, particularidad])`.
9. [ ] Si es no estándar, su ficha B1 pasa a "En uso" en el índice.

- **Columna**: In progress → In review → Done

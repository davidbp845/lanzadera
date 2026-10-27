# 1. Patrón multi-servicio

Para un proyecto que levanta varios procesos (caso de partida: Heruka Life).

1. **Script de arranque y de parada en el proyecto**, no en home. Estilo de `dev_up.sh`/`dev_down.sh`: `set -uo pipefail`, se autolocaliza con `BASH_SOURCE`, array de PIDs con `trap`, logs a `logs/`. Si solo existía un comando de Claude en prosa, primero se escribe el script.
2. **Arranque no interactivo**: un flag (`--skip-checks`) para saltarse cualquier `read -p`.
3. **`cmd_detener`** apuntando al script de parada: matar por el puerto principal no para procesos que se salen del grupo (p. ej. `astro dev`).
4. **`enlaces`** con todos los puertos: la UI muestra uno por servicio e `iniciar()` espera a todos.
5. **Puerto principal**: el del semáforo una vez arrancado. Que sea el del servicio que más tarda no es obligatorio (se espera a todos), pero sí lo más fiel.
6. **`intentos_espera_inicio`** medido en los logs del proyecto, con margen.
7. **Sub-servicios independientes** (Heruka Consola dentro de heruka-flow): fila propia con su par `cmd`/`cmd_detener`.

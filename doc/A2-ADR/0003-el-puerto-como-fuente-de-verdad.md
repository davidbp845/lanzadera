# 0003 — El puerto como fuente de verdad del estado

## Contexto

Un proyecto puede arrancarse desde home, desde una terminal o desde systemd. Guardar PIDs en home solo cubriría el primer caso, y se desfasaría tras un reinicio del launcher.

## Decisión

- **Activo** = el puerto principal acepta conexiones TCP en `127.0.0.1` (`connect_ex`, 0,3 s).
- **Parar sin `cmd_detener`** = `SIGTERM` al grupo de procesos de quien escucha el puerto (`ss -H -ltnp`).
- **Arrancar** termina cuando responden el puerto principal **y** todos los de `enlaces`, con un margen de `intentos_espera_inicio × 0,5 s`. Antes solo se esperaba al principal, y el panel de Heruka Life (el primero en abrir su puerto) ponía el semáforo en verde ~36 s antes de que respondiera el backend.
- Tras arrancar o parar se espera al cambio de estado antes del rerun, para que el semáforo no enseñe el estado viejo.

## Alternativas descartadas

- **Ficheros de PID** en `.launcher/`: no ven lo arrancado fuera de home.
- **Comprobar todos los puertos en cada carga**: más lento y no aporta mucho una vez arrancado; se usa solo el principal.

## Consecuencias

- Si otro proceso ocupa el puerto, el proyecto parece activo (riesgo en [9 — Riesgos](../A1-Vision/9-riesgos.md)).
- Un proyecto con un servicio caído pero el principal vivo se ve verde.

## Estado

Aceptada (espera a todos los puertos desde 2026-09-14). Ampliada por [0017](0017-lanzadera-en-windows-y-proyectos-sin-puerto.md).

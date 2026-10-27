# <n>. <Nombre> (`<slug>`)

> Estado: borrador / en uso

## 1. Qué es y dónde vive
Ruta relativa a `Data`, repo, si es submódulo de un contenedor.

## 2. Servicios y puertos
Cada servicio con su puerto. Cuál es el principal (el del semáforo) y por qué.

## 3. Arranque
Comando, entorno (`env`), si puede quedarse esperando entrada, si hay servicio de systemd.

## 4. Parada
Si basta matar a quien escucha el puerto y, si no, por qué y qué `cmd_detener` usa.

## 5. Tiempo hasta estar listo
Medido en los logs del proyecto, por servicio. `intentos_espera_inicio` resultante.

## 6. Choques conocidos
Puertos usados por otros, procesos parecidos que no hay que matar.

## 7. Verificación
Cómo se comprueba que el interruptor refleja la realidad y que la parada no deja huérfanos.

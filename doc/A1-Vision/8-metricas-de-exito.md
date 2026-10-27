# 8. Métricas de éxito

- **Cobertura**: todo proyecto de `Data/` con interfaz web está en el registro.
- **Semáforo fiel**: el estado mostrado coincide con el real tras arrancar o parar (sin verdes antes de que el último servicio responda).
- **Parada limpia**: tras parar, no quedan procesos huérfanos del proyecto (comprobable con `/uso-ram` o `ss -ltnp`).
- **Alta barata**: un proyecto estándar se da de alta solo con su fila en `datos/proyectos.toml`, sin tocar código.
- **Coste**: home en sí ocupa poca RAM (referencia: ~140 MB en `/uso-ram`).

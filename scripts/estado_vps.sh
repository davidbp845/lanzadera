#!/bin/sh
# Estado del VPS para la página VPS del launcher (ADR-0008). vps.py lo envía por
# stdin (`ssh <host> sh -s`), así que no se instala en el servidor. Solo lee.
# Cada bloque empieza con una línea "### <Sección>", que es por donde trocea vps.py;
# si falta el comando de una sección, la sección no se imprime.
LC_ALL=C
export LC_ALL

echo "### Sistema"
printf 'host     %s\n' "$(hostname)"
[ -r /etc/os-release ] && printf 'SO       %s\n' "$(. /etc/os-release && echo "$PRETTY_NAME")"
printf 'kernel   %s\n' "$(uname -r)"
printf 'uptime   %s\n' "$(uptime -p 2>/dev/null || uptime)"
printf 'carga    %s   (%s CPU)\n' "$(cut -d' ' -f1-3 /proc/loadavg)" "$(nproc)"

if command -v free >/dev/null; then
    echo "### Memoria"
    # Sin shared ni buff/cache: así cabe en una columna de la página, y available
    # es la que dice cuánta memoria queda de verdad.
    free -h | awk '
        NR == 1 { printf "%-6s %7s %7s %7s %10s\n", "", "total", "used", "free", "available"; next }
        { l = sprintf("%-6s %7s %7s %7s %10s", $1, $2, $3, $4, (NF >= 7 ? $7 : "")); sub(/ +$/, "", l); print l }'
fi

echo "### Disco"
df -h -x tmpfs -x devtmpfs -x overlay -x squashfs -x efivarfs 2>/dev/null

if command -v systemctl >/dev/null; then
    echo "### Servicios con fallo"
    fallidos=$(systemctl --failed --no-legend --plain 2>/dev/null)
    if [ -n "$fallidos" ]; then
        echo "$fallidos"
    else
        echo "0 servicios con fallo"
    fi
fi

echo "### Procesos con más RAM"
ps -eo pid,user,%mem,rss,comm --sort=-rss | head -n 6 | awk '
    NR == 1 { printf "%7s %-10s %5s %7s %s\n", "PID", "USER", "%MEM", "RSS", "COMMAND"; next }
    { printf "%7s %-10s %5s %6dM %s\n", $1, $2, $3, $4 / 1024, $5 }'

if command -v docker >/dev/null; then
    echo "### Contenedores"
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>&1
fi

# Las distribuciones recientes sustituyen last por wtmpdb.
if command -v last >/dev/null; then
    echo "### Últimos accesos"
    # Tras los registros, last añade una línea en blanco y "wtmp begins…".
    last -n 5 2>/dev/null | sed '/^$/,$d'
elif command -v wtmpdb >/dev/null; then
    echo "### Últimos accesos"
    wtmpdb last -n 5 2>/dev/null | sed '/^$/,$d'
fi

# El estado de salida del último `command -v` no es un fallo de la consulta.
exit 0

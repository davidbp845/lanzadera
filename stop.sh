#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PID=$(pgrep -f "streamlit run app.py" | while read -r p; do
  [ "$(readlink -f /proc/$p/cwd)" = "$(pwd -P)" ] && echo "$p"; done || true)

if [ -z "$PID" ]; then
  echo "El launcher no está en ejecución."
else
  kill $PID
  echo "Launcher detenido (PID $PID)."
fi

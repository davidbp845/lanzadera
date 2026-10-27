#!/usr/bin/env bash
# Launcher en http://localhost:8501 (puerto en .streamlit/config.toml). Normalmente lo
# arranca el servicio home-streamlit (deploy/home-streamlit.service): esto es para desarrollo.
set -e
cd "$(dirname "$0")"

venv/bin/python -m streamlit run app.py "$@"

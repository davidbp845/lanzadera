@echo off
rem Launcher en Windows en http://localhost:8501 (puerto en .streamlit\config.toml), ADR-0017.
rem Entorno virtual propio, venv-windows\: venv\ es el de Linux y la carpeta puede estar
rem compartida entre los dos sistemas. Los datos salen de HOME_LAUNCHER_DATOS o de ..\datos.
cd /d "%~dp0"
if not exist venv-windows\Scripts\python.exe (
  py -3 -m venv venv-windows || exit /b 1
  venv-windows\Scripts\python -m pip install -r requirements.txt || exit /b 1
)
venv-windows\Scripts\python -m streamlit run app.py %*

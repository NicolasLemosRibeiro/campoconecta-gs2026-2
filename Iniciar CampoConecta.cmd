@echo off
setlocal
cd /d "%~dp0"
uv run --no-project --python 3.12 python "%~dp0iniciar_integrado.py" %*
if errorlevel 1 pause

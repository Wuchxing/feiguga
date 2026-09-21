@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist "assets_processed\01-core-standard.png" (
  call .venv\Scripts\python.exe process_assets.py
)
call .venv\Scripts\python.exe main.py

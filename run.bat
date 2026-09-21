@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)

call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist "assets_processed\01-core-standard.png" (
  call .venv\Scripts\python.exe process_assets.py
  if errorlevel 1 goto :error
)

start "" ".venv\Scripts\pythonw.exe" "%~dp0main.py"
exit /b 0

:error
echo.
echo 启动失败，错误代码：%errorlevel%
pause
exit /b 1

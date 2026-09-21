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

call .venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name FeigugaPet --add-data "assets_processed;assets_processed" main.py
if errorlevel 1 goto :error

echo.
echo EXE 已生成到 dist\FeigugaPet\FeigugaPet.exe
pause
exit /b 0

:error
echo.
echo 构建失败，错误代码：%errorlevel%
echo 请保留本窗口中的错误信息。
pause
exit /b 1

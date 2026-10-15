@echo off
setlocal
cd /d "%~dp0\.."
echo [PhoneHUB] Preparando build Windows...
where py >nul 2>nul
if errorlevel 1 (echo [ERRO] Python Launcher nao encontrado. Instale Python 3.11+ e marque Add to PATH.& exit /b 1)
py -3 -m venv .venv-build
if errorlevel 1 exit /b 1
.venv-build\Scripts\python.exe -m pip install --upgrade pip pyinstaller
if errorlevel 1 exit /b 1
.venv-build\Scripts\python.exe -m pip install -e .
if errorlevel 1 exit /b 1
.venv-build\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name PhoneHUB --paths src main.py
if errorlevel 1 exit /b 1
.venv-build\Scripts\pyinstaller.exe --noconfirm --clean --console --name PhoneHUB-console --paths src main.py
if errorlevel 1 exit /b 1
echo.
echo [OK] Builds em dist\PhoneHUB.exe e dist\PhoneHUB-console.exe
echo NOTA: ADB e scrcpy sao dependencias externas e nao estao embutidos automaticamente.
endlocal

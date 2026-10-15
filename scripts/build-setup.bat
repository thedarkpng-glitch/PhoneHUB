@echo off
setlocal
cd /d "%~dp0\.."
if not exist installer\release_url.txt (echo [ERRO] Crie installer\release_url.txt com a URL HTTPS direta do PhoneHUB.exe.& exit /b 1)
set /p RELEASE_URL=<installer\release_url.txt
if "%RELEASE_URL%"=="" (echo [ERRO] release_url.txt esta vazio.& exit /b 1)
echo [PhoneHUB] Compilando bootstrapper. URL configurada: %RELEASE_URL%
if not exist .venv-build\Scripts\pyinstaller.exe (echo [ERRO] Rode scripts\build-windows.bat primeiro para preparar o ambiente de build.& exit /b 1)
set PHONEHUB_RELEASE_URL=%RELEASE_URL%
.venv-build\Scripts\pyinstaller.exe --noconfirm --clean --onefile --windowed --name setup --add-data "installer\release_url.txt;." installer\setup_bootstrapper.py
if errorlevel 1 exit /b 1
echo [OK] dist\setup.exe
endlocal

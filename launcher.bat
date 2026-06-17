@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "APP_URL=http://127.0.0.1:8000"

cd /d "%PROJECT_DIR%"

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python en el PATH.
    echo Instala Python o agrega python.exe al PATH de Windows.
    pause
    exit /b 1
)

start "Sistema Operacional-Financiero - Servidor" cmd /k "cd /d ""%PROJECT_DIR%"" && python src\webapp.py"

timeout /t 3 /nobreak >nul
start "" "%APP_URL%"

endlocal

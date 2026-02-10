@echo off
echo ======================================
echo   ContaSystem - Sistema de Gestion   
echo ======================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no esta instalado
    echo Por favor instala Python 3.8 o superior
    pause
    exit /b 1
)

echo Python encontrado
echo.

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Dependencias instaladas
echo.

REM Iniciar aplicacion
echo Iniciando ContaSystem...
echo.
echo Accede a la aplicacion en: http://localhost:8000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python app.py
pause

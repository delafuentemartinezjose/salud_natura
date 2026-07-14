@echo off
cd /d "%~dp0"

echo.
echo  Salud Natura - Subiendo cambios a GitHub...
echo  -----------------------------------------------

git add .
git status

echo.
set /p MSG="  Descripcion del cambio (Enter para usar 'actualizacion'): "
if "%MSG%"=="" set MSG=actualizacion

git commit -m "%MSG%"
git push origin main

echo.
echo  -----------------------------------------------
echo  Listo! Cambios subidos a GitHub.
echo.
echo  Recuerda: conectate al servidor y ejecuta:
echo    cd salud_natura ^&^& git pull
echo    systemctl restart saludnatura
echo.
pause

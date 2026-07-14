@echo off
cd /d "%~dp0"
for /f "tokens=1-5 delims=/ " %%a in ("%date%") do set FECHA=%%c-%%b-%%a
for /f "tokens=1-2 delims=:." %%a in ("%time%") do set HORA=%%a:%%b
git add .
git commit -m "actualizacion %FECHA% %HORA%"
git push origin main

@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Vista previa del album (en tu ordenador, sin publicar)...
echo  Para publicar no hace falta esto: basta con subir las fotos a GitHub.
echo.
set PY=python
where python >nul 2>nul || set PY=py
%PY% -m pip install --quiet --disable-pip-version-check pillow pillow-heif
%PY% herramientas\build.py
echo.
start "" "_web\index.html"
pause

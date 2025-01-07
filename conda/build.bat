@echo off

echo %SP_DIR%
echo %RECIPE_DIR%
dir %RECIPE_DIR%\..

mkdir %SP_DIR%\map2loop
copy %RECIPE_DIR%\..\dependencies.txt %SP_DIR%\map2loop\
%PYTHON% -m pip install . --no-deps
@echo on 
echo "SP_DIR: %SP_DIR%"
echo "RECIPE_DIR: %RECIPE_DIR%"

dir %RECIPE_DIR%\..

mkdir %SP_DIR%\map2loop
copy %RECIPE_DIR%\..\dependencies.txt %SP_DIR%\map2loop\
%PYTHON% -m pip install . --no-deps
mkdir %SP_DIR%\map2loop
copy %RECIPE_DIR%\..\LICENSE %SP_DIR%\map2loop\
copy %RECIPE_DIR%\..\README.md %SP_DIR%\map2loop\
copy %RECIPE_DIR%\..\dependencies.txt %SP_DIR%\map2loop\
%PYTHON% -m pip install . --no-deps
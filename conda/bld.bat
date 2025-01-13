mkdir %SP_DIR%\map2loop
copy %RECIPE_DIR%\..\LICENSE %SP_DIR%\map2loop\
copy %RECIPE_DIR%\..\README.md %SP_DIR%\map2loop\
copy %RECIPE_DIR%\..\dependencies.txt %SP_DIR%\map2loop\
<<<<<<< HEAD
<<<<<<< HEAD
%PYTHON% -m pip install . 
=======
%PYTHON% -m pip install . --no-deps
>>>>>>> b33532b (fix: include dependencies in site-packages  - issue #169 (#170))
=======
%PYTHON% -m pip install . 
>>>>>>> 9ca260f (chore: typo in conda build (#176))

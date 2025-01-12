#!/bin/bash
mkdir -p $SP_DIR/map2loop
cp $RECIPE_DIR/../dependencies.txt $SP_DIR/map2loop/
cp $RECIPE_DIR/../LICENSE $SP_DIR/map2loop/
cp $RECIPE_DIR/../README.md $SP_DIR/map2loop/
<<<<<<< HEAD
$PYTHON -m pip install . 
=======
$PYTHON -m pip install . --no-deps
>>>>>>> b33532b (fix: include dependencies in site-packages  - issue #169 (#170))

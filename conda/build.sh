#!/bin/bash
mkdir -p $PREFIX/share/map2loop
cp $RECIPE_DIR/../dependencies.txt $PREFIX/share/map2loop/
$PYTHON -m pip install . --no-deps

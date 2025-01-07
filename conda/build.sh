#!/bin/bash
mkdir -p $SP_DIR/map2loop
cp $RECIPE_DIR/../dependencies.txt $SP_DIR/map2loop/
$PYTHON -m pip install . --no-deps

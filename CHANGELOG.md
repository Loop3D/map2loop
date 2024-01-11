# Changelog

## [5.0.0](https://github.com/Loop3D/map2loop-3/compare/v4.0.0...5.0.0) (2024-01-11)


### ⚠ BREAKING CHANGES

* Force release-please

### Features

* Add new stratigraphic column sorters based on contact length and unit relationships fix: transpose dtm for height calculations, export geotiff using gdal ([36ddcca](https://github.com/Loop3D/map2loop-3/commit/36ddcca650d7f12c102b77e5df23d7a2b7710ee3))
* Allow for empty dataframes if no filename specified. Mainly for fault and fold files ([f81d9b4](https://github.com/Loop3D/map2loop-3/commit/f81d9b4496a9d863864f72d2c1d2813871bccb24))
* Force release-please ([5969f94](https://github.com/Loop3D/map2loop-3/commit/5969f946effb3a5c25fdf1a36c9406d39844e109))


### Bug Fixes

* Add special case for SA config file to lowercase the column names.  Also check for empty map2model relationship files and deal appropriately with them ([82054df](https://github.com/Loop3D/map2loop-3/commit/82054dfec9f82b353a63b42e5f3d815fdeff5fee))
* Added new stratigraphic sorters, a placeholder for throw calculators and updated thickness calculator ([e08e010](https://github.com/Loop3D/map2loop-3/commit/e08e010f38070c175412f0b92946b5ce705c5409))
* conda build needs testing env now ([b674d6a](https://github.com/Loop3D/map2loop-3/commit/b674d6a4c69baf9f4a9865c4d7191417dce8719b))
* Default temp path changed to work in linux ([5bd773b](https://github.com/Loop3D/map2loop-3/commit/5bd773bdd27268aa8b516b799a16dca141056c0f))
* Dependencies issue with new version of geopandas breaking read_file on remote zip files. Also, fixed errant line that installed the old version of map2model ([4eb720a](https://github.com/Loop3D/map2loop-3/commit/4eb720a2d766b821d0cf31e46bc8b3f571ea6fc7))
* new flake8 compliance ([6776e25](https://github.com/Loop3D/map2loop-3/commit/6776e25a4c22faf483ffd70010202211b0b874b2))
* revert hjson back to loop3d version as hjson-py does not work ([84b846a](https://github.com/Loop3D/map2loop-3/commit/84b846ae8efd293428acb2bb1c4515f0f48e6a31))
* Revert version to correct version for release ([6de8400](https://github.com/Loop3D/map2loop-3/commit/6de840029d5de647a95526ed47cdad7edca1ac49))
* Use geology sampler for contact sampling ([615d19a](https://github.com/Loop3D/map2loop-3/commit/615d19adefddeb736871ed4b4ad5329e8b1ac9e8))

## [4.0.0](https://github.com/Loop3D/map2loop-3/compare/3.0.1...4.0.0) (2024-01-11)


### ⚠ BREAKING CHANGES

* Force release-please

### Features

* Force release-please ([5969f94](https://github.com/Loop3D/map2loop-3/commit/5969f946effb3a5c25fdf1a36c9406d39844e109))

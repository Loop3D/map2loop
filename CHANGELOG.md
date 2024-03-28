# Changelog

## [3.0.7](https://github.com/Loop3D/map2loop/compare/3.0.6...v3.0.7) (2024-03-28)


### Bug Fixes

* Add exception handling around hjson access ([#24](https://github.com/Loop3D/map2loop/issues/24)) ([f627f83](https://github.com/Loop3D/map2loop/commit/f627f83079ba0c1315fc59d98fc2bb2fe27a0191))
* Add exception handling around hjson access, throw with better message ([d8804de](https://github.com/Loop3D/map2loop/commit/d8804de89a9ecc8705914f959b3c4a4858f968d9))
* Add layer id to structural data using a spatial join ([#38](https://github.com/Loop3D/map2loop/issues/38)) ([09c53d6](https://github.com/Loop3D/map2loop/commit/09c53d6fbb6b44c46b9e88cf9044f7ccd1ebd555))
* Add multiple tries to online config file access ([8a137ce](https://github.com/Loop3D/map2loop/commit/8a137cedc298596ea4ce858a5ff4e256eb169b7c))
* adding empty samples to project class ([bf100b2](https://github.com/Loop3D/map2loop/commit/bf100b2c23a284072d11d54e080d882da0460942))
* adding fault orientation calculation ([e35f0b6](https://github.com/Loop3D/map2loop/commit/e35f0b6a78ae85482a66f6636b54bc079432dd51))
* adding fault orientation calculator ([08c9f5e](https://github.com/Loop3D/map2loop/commit/08c9f5e943ee31b52ca613c4da44b3521018eb22))
* adding fault orientation data type ([f0e82e2](https://github.com/Loop3D/map2loop/commit/f0e82e20553f7f930ea4237c7516a18c61907090))
* adding orientation type to fault config. ([6359937](https://github.com/Loop3D/map2loop/commit/635993739bac4acf5c6e6ad83a884c391602285c))
* adding to_dict for config ([968504e](https://github.com/Loop3D/map2loop/commit/968504e27e56b343feee58a8a1ed297f493c5d87))
* adding to_dict for config ([968504e](https://github.com/Loop3D/map2loop/commit/968504e27e56b343feee58a8a1ed297f493c5d87))
* adding to_dict for config ([258254e](https://github.com/Loop3D/map2loop/commit/258254e7fc4e2628c035a400083c04dc4f81866b))
* adding version and ignoring init file for f401 ([db6ac5b](https://github.com/Loop3D/map2loop/commit/db6ac5b48f7ade6d57b2a6a094811c083c996bd0))
* changing boolean comparison ([d90df18](https://github.com/Loop3D/map2loop/commit/d90df183cb9042a994525cfd698297aa588ea04f))
* changing isinstance to issubclass ([0e9ecc8](https://github.com/Loop3D/map2loop/commit/0e9ecc82b37a0a979aefc8fb3ae83b406f30a37a))
* Check for empty dataframe before concat ([c475513](https://github.com/Loop3D/map2loop/commit/c475513c84c356d1a2b09bcd331c861f124b3317))
* default fault dip/dipdir to nan ([917cee6](https://github.com/Loop3D/map2loop/commit/917cee6bc7c27ed18a067403e7780d54656f92f5))
* default fault values to nan not 0 to prevent unexpected behaviours ([87863c7](https://github.com/Loop3D/map2loop/commit/87863c76654da4fee87fed45ac5015e30c49defa))
* letting docs build run on docker ([8b4ade0](https://github.com/Loop3D/map2loop/commit/8b4ade0675aa5d497cbd469a85f59b1d19b09239))
* removing commented code ([22db166](https://github.com/Loop3D/map2loop/commit/22db1668448e088fa02caa4f5bd2e17980774dc2))
* renaming compute to calculate ([f5a0ffb](https://github.com/Loop3D/map2loop/commit/f5a0ffb3beeb6c59dc2c3758bcc7251a74cea9a1))
* Reworked dataframe to avoid chained assignment ([77b322f](https://github.com/Loop3D/map2loop/commit/77b322f5daccbf74d316bd6adfd3e1dd70e47d5e))
* ruff linter and docs fix ([c7e42a6](https://github.com/Loop3D/map2loop/commit/c7e42a68e4824ee1eff7a0c8c8797e1c2b7365db))
* Typo fix for config dictionary converter ([15b543b](https://github.com/Loop3D/map2loop/commit/15b543bc077550c683c94d7bb97a74389b1de29e))
* typo in calculate ([c0ec36b](https://github.com/Loop3D/map2loop/commit/c0ec36b2444fb136b80e0356debf5f13ad454258))
* updated docstring ([93d47bf](https://github.com/Loop3D/map2loop/commit/93d47bfac84397cf842a9398d1b0bd0dae873c5b))


### Documentation

* Add import modules and example parameters to sorter and thickness calculator docs. ([3ed1ea7](https://github.com/Loop3D/map2loop/commit/3ed1ea73128bcce142fbd84a38947fd99b24332e))
* Add import modules and example parameters to sorter and thickness calculator docs. ([#33](https://github.com/Loop3D/map2loop/issues/33)) ([b4e6247](https://github.com/Loop3D/map2loop/commit/b4e6247117baf012009c7a81c4b923beb38bef5c))
* adding aylas code template ([48c1093](https://github.com/Loop3D/map2loop/commit/48c10935654b35aef191c160aa7c2cb69dc38332))
* adding documentaion to map2loop ([2a30da4](https://github.com/Loop3D/map2loop/commit/2a30da44329d0adc0eb8026e861c7cc8fa23ffac))
* adding hjson file ([1d03505](https://github.com/Loop3D/map2loop/commit/1d03505debdf67ce2e7bc313e935173ed6868f38))
* adding m2l template ([b2f8ea0](https://github.com/Loop3D/map2loop/commit/b2f8ea0dd92455d5106a5d8260e56053ac5e2199))
* adding user guide ([47c8d9b](https://github.com/Loop3D/map2loop/commit/47c8d9b939d303ae7f68832c1550bd8da1735bca))
* adding user guide for map2loop  ([57c2263](https://github.com/Loop3D/map2loop/commit/57c22633d46d598f9a013e09984287a2a9953535))
* Fixed indentation of code block ([5be5208](https://github.com/Loop3D/map2loop/commit/5be5208d0e3121ce3328dcc788309d7e81d7c199))
* fixing path to images ([6b311d6](https://github.com/Loop3D/map2loop/commit/6b311d6a6f3ce53e896c39e620823285b0ff79db))
* geographical --&gt; geological ([b368c19](https://github.com/Loop3D/map2loop/commit/b368c196e31484c023a21b2b61b6c6b2c8c9f2e0))
* making code block work ([d0ed967](https://github.com/Loop3D/map2loop/commit/d0ed967eede6cab6373da3d92dfcdf7d004b678c))
* Move examples dir for doc generation ([241444f](https://github.com/Loop3D/map2loop/commit/241444fabf3bba69c8fdfbee279cef6d97b01f04))
* moving images ([a800455](https://github.com/Loop3D/map2loop/commit/a800455496e92c34853e82bef618ee541072358f))
* removing LS import for config ([bcee039](https://github.com/Loop3D/map2loop/commit/bcee03998035ae92cb48dd2d02f921ce39bed91b))

## [3.0.6](https://github.com/Loop3D/map2loop/compare/3.0.5...3.0.6) (2024-01-25)


### Bug Fixes

* Remove deprecation ignore warnings and then deprecations ([79cd333](https://github.com/Loop3D/map2loop/commit/79cd33317625c96091690c9b97309be74cba2fdd))

## [3.0.5](https://github.com/Loop3D/map2loop/compare/3.0.4...3.0.5) (2024-01-25)


### Bug Fixes

* Typo in intrusion flag, ignoring intrusions for contact calculations, remove errant sorter from take_best option ([527de6c](https://github.com/Loop3D/map2loop/commit/527de6c339e56ead036ab5ed5d94d06d77673ae6))

## [3.0.4](https://github.com/Loop3D/map2loop-3/compare/3.0.3...3.0.4) (2024-01-11)


### Bug Fixes

* Issue with conda build test env not working, skipping ([2fffb69](https://github.com/Loop3D/map2loop-3/commit/2fffb696556f48f0620dfbac356971301fb15e89))

## [3.0.3](https://github.com/Loop3D/map2loop-3/compare/3.0.2...3.0.3) (2024-01-11)


### Bug Fixes

* Add owslib as dependency for testing ([0439da8](https://github.com/Loop3D/map2loop-3/commit/0439da869856b187defbed631c592a848b3684a1))

## [3.0.2](https://github.com/Loop3D/map2loop-3/compare/3.0.1...3.0.2) (2024-01-11)


### Bug Fixes

* Still forcing versioning for release-please ([08e647b](https://github.com/Loop3D/map2loop-3/commit/08e647bac1dded0c807bbb9a3571a741505bd488))

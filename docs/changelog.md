# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format. 

## [0.8.0] - 2020-06-25

### Added
- plugins functionality

### Changed
- dropped Python 2 support

### Removed
- preciously deprecated `get_asset` method. Use `seek` instead

## [0.7.0] - 2020-03-17

### Added
- `RefGenConf` methods update the file on disk that's bound to the object if one exists
- `seek` method. Works similarily to `get_asset`, but does not check for asset file existence on disk by default.

### Changed
- `RefGenConf` method names to match the `refgenie` (CLI) terminology
	- `remove_assets` to `remove`
	- `asset_dict` to `list`
	- `list_remote` to `listr`
	- `tag_asset` to `tag`
	- `pull_asset` to `pull`
	- `get_asset_digest` to `id`
  	- `get_asset` to `seek`. Moreover the file existence 

### Deprecated
- `get_asset` method. Use `seek` instead

## [0.6.2] - 2020-01-15

### Added
- `genome_archive_config` key to the genome configuration file

### Changed
- `genome_archive` key to `genome_archive_folder` in the config file. 

## [0.6.1] - 2019-12-13

### Added
- `remove_asset_from_relatives` method for assets' relationship links removal
- `initialize_config_file` method

### Changed
- `remove_assets` method removes the asset relatives links
- in `select_genome_config` function the `filepath` argument is not required anymore; the `$REFGENIE` environment variable can used instead

## [0.6.0] - 2019-12-06

### Added
- `get_asset_digest` method for asset digest retrieval
- `dir` to the `filepath` method to return an archive enclosing directory
- `get_asset_digest` method to return the digest for the specified asset
- `update_genome_servers` method for `genome_servers` attribute manipulation 

### Changed
- `pull_asset` method so that it downloads the archive from a server, makes the object writable, updates it and writes the updates to the refgenie configuration file on disk
- the way of distribution of `refgenieserver` endpoints operationIds. They are grouped and mapped to a short description   

### Fixed
- overloaded colon in progress bar descriptions; [#73](https://github.com/databio/refgenconf/issues/73)

## [0.5.4] - 2019-11-05

### Added
- distribute the license file with the package

## [0.5.3] - 2019-10-29

### Changed
- `genome_server` config key to `genome_servers`
- enable multiple refgenieservers for `pull_asset` method
- `_chk_digest_if_avail` and `_chk_digest_update_child` require server URL argument to get the asset information from

## [0.5.2] - 2019-10-22

### Changed
- required `yacman` version, for safer file locking

## [0.5.1] - 2019-10-19

### Fixed
- small bug in documentation that prevented automatic doc builds

## [0.5.0] - 2019-10-19

### Added
- systematic determination of `refgenieserver` API endpoint names
- asset provenance assertion before pull
- asset tagging support
- asset relationship tracking
- asset removal method

### Changed
- no config file updates after pull
- config format; added sections for storing digests, tags, parent and children info


## [0.4.0] - 2019-07-02

### Added
- `remove_assets` method
- local and remote listing restriction by genome. These methods accept an optional `genome` argument:
    - `list_local`
    - `list_remote`
    - `assets_dict`
    - `assets_str`

## [0.3.0] - 2019-07-11
### Changed
- Favor asset path relative to genome config rather than local folder in case both exist.
- `update_genomes` method renamed to `update_assets`
- genome config file format changes:
    - Added `config_version` entry
    - Added `assets` section in `genomes` section

### Added
- `udpate_genomes` method
- Genome config file version is now verified in `RefGenConf.__init__` 

## [0.2.0] - 2019-06-18
### Added
- Ability to control behavior when pulled asset already exists
- Hook for ordering most of the config query results
### Changed
- By default, alphabetize returned results (genomes, assets, and assets by genome).

## [0.1.2] - 2019-06-11
### Fixed
- Logic path such that genome config file is updated regardless of asset unpacking

## [0.1.1] - 2019-06-11
### Fixed
- [Double-slash bug](https://github.com/databio/refgenie/issues/51) in URLs

## [0.1.0] -- 2019-06-10
- Initial project release

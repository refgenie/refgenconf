# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format. 

## [0.5.3] - unreleased

### Changed
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

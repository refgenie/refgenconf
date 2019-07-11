# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format. 

## [0.2.1] - Unreleased
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

# Changelog
All notable changes to this project will be documented in this file.


## [Unreleased]
## [0.1.8] - 2020-04-01
### Changed
* Trivially changed utils._xlate_from_js to utils._xlate_from_camel_case
  for clarity.

## [0.1.8] - 2020-04-01
### Added
- Add support for uuids to strings in serialization.
- Added exposure of engine as an attribute of DB
- Added CHANGELOG file.

### Changed
- Separated functions `create_database` and `drop_database` from base to maint module
- Reworked how Model gets updated upon instantiating with DB.

### Fixed
- Cleaned up typos in documentation.

### Removed
- Removed an unnecessary test, `verify_requireds`, from tests -- fixture_base
  It was unnecessary for a base installation.

## [0.1.8] - 2020-03-23
### Added
- Initial public release


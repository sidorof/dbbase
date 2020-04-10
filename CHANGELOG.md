# Changelog
All notable changes to this project will be documented in this file.


## [Unreleased]
## [0.1.9] -
### Changed
* Trivially changed utils._xlate_from_js to utils._xlate_from_camel_case
  for clarity.
* Fixed Model._class() function. When used as part of a Python package, it
  identified the class as DeclarativeMeta rather than the correct class
  name. Also, it now works for Postgres materialized views.
* Changed Model._get_serial_stop_list from a class method. It is only
  useful with an instance.
* Added to Model.to_dict and Model.serialize a parameter, `serial_list`,
  `serial_list` enables displacing the class `SERIAL_LIST` attribute for
  on an ad hoc basis to the fields that are included in serialization.
* Added a class attribute, `RELATION_SERIAL_LISTS`, to better control the
  output of relations. The new variable is a dict where the key is a
  relationship field and the value is the explicit list of fields that
  would be included in serialization. The advantage is that a standard
  list of fields for the secondary relationship variable does not have to
  define the output for the primary serialization. Just as a `serial_list`
  parameter has been added to Model.to_dict and Model.serialize, a
  `relation_serial_lists` has been added as well for convenience.

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


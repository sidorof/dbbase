# Changelog

## [0.1.15] -
### Changed
*   Changed conversion of UUIDs conversion to strings to remove hyphens.
    A serialized uuid is shortened from `1f4fdf7e-6f8d-4a7e-b0bd-7ae0722b324d`
    to `1f4fdf7e6f8d4a7eb0bd7ae0722b324d`.

## [0.1.14] -
### Added
*   Added a function `validate_record` to the Model class. The
    initial version evaluates a record by comparing columns defined as required
    that do not have default values filled in. Of course more issues can
    contribute to a failure to save a record, but it is a start. It also
    has the ability to return the error message in camel case for front end
    use.
    The expected usage:

```python
        status, errors = self.validate_record()
        if status:
            self.save()
        else:
            return errors
```
*  Added a `delete` function to the Model class.

```python

  # dbbase
  user = User(name='Bob')
  User.save()

  # then delete
  user.delete()
```


## [0.1.13] -
### Added
*   Added conversion from bytes as well as strings for the
    deserialization function. This aids in conversion for
    query_strings received, eliminating a step.

## [0.1.12] -
### Removed
*   Removed tests again. Included more thorough approach.

## [0.1.11] -
### Removed
*   Removed tests, docs, docsrc from setup.py


## [0.1.10] -
### Changed
*   Changed base._apply_db to recognize materialized views as well as
    regular tables.


## [0.1.9] -
### Added
* Added to `Model.to_dict` and `Model.serialize` a parameter, `serial_list`,
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

### Changed
* Trivially changed utils._xlate_from_js to utils._xlate_from_camel_case
  for clarity.
* Changed `Model._get_serial_stop_list` from a class method. It is only
  useful with an instance.

### Fixed
* Fixed `Model._class()` function. When used as part of a Python package, it
  identified the class as DeclarativeMeta rather than the correct class
  name. Also, it now works for Postgres materialized views.


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


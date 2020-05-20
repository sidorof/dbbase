# Changelog
## (0.2.3) -
### Changed
*   Changed the name of SERIAL_LIST to SERIAL_FIELDS, and RELATION_SERIAL_LISTS to SERIAL_FIELD_RELATIONS to better describe what they are. The parameters associated with using these variables are changed as well.

## (0.2.2) -
### Added
* Added `db.doc_column` function that returns the documentation dictionary for a specific column.
* Added checking for valid foreign keys in `Model.validate_record`. Prior to attempting a save, the columns  that cannot be null, and require foreign key validation are verified against the foreign table.

## (0.2.1) -
### Added
*   Added model documentation properties for functions, properties, and relationships. All of these are marked as readOnly: True. This additional feature gives a more complete picture of the characteristics of the model. Just as serialization is shaped by the function, `Model._get_serial_stop_list()`, only those items which pass that hurdle will be documented. That filter ensures that only meaningful items will be documented.
*   Added model documentation properties for table constraints

### Fixed
*   Added `__repr__` and `__table__` to default stop lists

## (0.2.0) -
### Added
*   Added `db.doc_table()` and `db.doc_tables()` function to help build documentation for table
    objects in a way that is reminiscent of Swagger / OpenApi.

    For example, here is the output in JSON format using the approach that
    OpenApi takes. In fact, there are some differences. These differences
    stem from the more nuanced approach that SQLAlchemy takes for things like
    defaults. For example, server side defaults are specified. Also, on update functions are detailed as well.

    Usage:

```python
    doc_table(
        cls,                   # the class
        to_camel_case=False,   # convert column names to camel case
        serial_list=None,      # select only specific columns
        column_props=None      # select only certain column properties
    )
```
Some uses for this function:
*   Detail on the tables can be part of a larger communication with
    developers using an API.
*   Meta information can be resourced about particular views.
*   Unit / integration tests can use the output to ensure that table
    columns are created to specifications.

Here is an example of some of the column types that are tested.

```json

    {
        "SampleTable": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "format": "int32",
                    "primary_key": true,
                    "nullable": true,
                    "comment": "Primary key with a value assigned by the database",
                    "info": {
                        "extra": "info here"
                    }
                },
                "name1": {
                    "type": "string",
                    "maxLength": 50,
                    "nullable": false,
                    "comment": "This field is required",
                    "info": {}
                },
                "indexValue": {
                    "type": "integer",
                    "format": "int32",
                    "nullable": true,
                    "server_default": {
                        "for_update": false,
                        "arg": "db.text(\"0\")",
                        "reflected": false
                    },
                    "comment": "This field defaults to an integer on the server.",
                    "info": {}
                },
                "createdAt1": {
                    "type": "date-time",
                    "nullable": true,
                    "default": {
                        "for_update": false,
                        "arg": "datetime.now"
                    },
                    "comment": "This field defaults to now, created at model level",
                    "info": {}
                },
                "updateTime1": {
                    "name": "update_time1",
                    "type": "date-time",
                    "nullable": true,
                    "onupdate": {
                        "for_update": true,
                        "arg": "datetime.now"
                    },
                    "comment": "This field defaults only on updates",
                    "info": {}
                },
                "uniqueCol": {
                    "type": "string",
                    "maxLength": 20,
                    "nullable": true,
                    "unique": true,
                    "comment": "This must be a unique value in the database.",
                    "info": {}
                },
                "name2": {
                    "type": "string",
                    "maxLength": 50,
                    "nullable": true,
                    "comment": "This field is not required",
                    "info": {}
                },
                "fkId": {
                    "type": "integer",
                    "format": "int32",
                    "nullable": false,
                    "foreign_key": "other_table.id",
                    "comment": "This field is constrained by a foreign key on another table",
                    "info": {}
                },
                "someSmallInt": {
                    "type": "integer",
                    "format": "int8",
                    "nullable": false,
                    "default": {
                        "for_update": false,
                        "arg": 0
                    },
                    "comment": "This field is a small integer",
                    "info": {}
                },
                "someInt": {
                    "type": "integer",
                    "format": "int32",
                    "nullable": false,
                    "default": {
                        "for_update": false,
                        "arg": 0
                    },
                    "comment": "This field is a 32 bit integer",
                    "info": {}
                },
                "today": {
                    "type": "date",
                    "nullable": true,
                    "default": {
                        "for_update": false,
                        "arg": "date.today"
                    },
                    "doc": "this is a test",
                    "comment": "This field defaults to today, created at model level",
                    "info": {
                        "test": "this is"
                    }
                },
                "someBigInt": {
                    "name": "some_big_int",
                    "type": "integer",
                    "format": "int64",
                    "nullable": false,
                    "default": {
                        "for_update": false,
                        "arg": 0
                    },
                    "comment": "This field is a big integer",
                    "info": {}
                },
                "statusId": {
                    "type": "integer",
                    "format": "int32",
                    "choices": {
                        "0": "New",
                        "1": "Active",
                        "2": "Suspended",
                        "3": "Inactive"
                    },
                    "nullable": false,
                    "comment": "Choices from a list. String descriptors change to integer upon saving. Enums without the headache.",
                    "info": {}
                },
                "name3": {
                    "type": "text",
                    "nullable": false,
                    "default": {
                        "for_update": false,
                        "arg": "test"
                    },
                    "index": true,
                    "comment": "This field has a default value",
                    "info": {}
                },
                "itemLength": {
                    "type": "float",
                    "nullable": false,
                    "comment": "This field is a float value",
                    "info": {}
                },
                "abc": {
                    "type": "string",
                    "maxLength": 20,
                    "nullable": true,
                    "server_default": {
                        "for_update": false,
                        "arg": "abc",
                        "reflected": false
                    },
                    "comment": "This field defaults to text but on the server.",
                    "info": {}
                },
                "itemAmount": {
                    "name": "item_amount",
                    "type": "numeric(17, 6)",
                    "nullable": true,
                    "default": {
                        "for_update": false,
                        "arg": 0.0
                    },
                    "info": {}
                },
                "updateTime2": {
                    "type": "date-time",
                    "nullable": true,
                    "server_onupdate": {
                        "for_update": true,
                        "arg": "db.func.now()",
                        "reflected": false
                    },
                    "comment": "This field defaults only on updates, but on the server",
                    "info": {}
                },
                "createdAt2": {
                    "type": "date-time",
                    "nullable": true,
                    "server_default": {
                        "for_update": false,
                        "arg": "db.func.now()",
                        "reflected": false
                    },
                    "comment": "This field defaults to now, created at the server level",
                    "info": {}
                }
            },
            "xml": "SampleTable"
        }
    }

```

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


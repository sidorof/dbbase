## Introduction

**dbbase** implements a light-weight wrapper around SQLAlchemy in the style of Flask-SQLAlchemy, but without the requirements of Flask. So the same models and classes used in a Flask project can be used in other contexts than web applications.

The package focuses on three areas of interest.

* Convenience functions as part of the Model class with easy access to the session and query object, as well as simple functions for saving, etc. within the Model class.

* Serialization functions enable expressing model data as both JSON and dictionary objects. This feature facilitates easy access to views. The views can be scaled up to include objects created by relationships with explicit control over the content, or show only the bare minimum. These functions can be used as part of an API.

* Document dictionaries introspect the model classes you have built and present the data objects in a format similar to Swagger / OpenAPI. This enables a method for communicating the details of the models. In addition, the functions could be wrapped into parsing functions that evaluate query strings and form data, directly from the table characteristics. This avoids the extra work of defining tables, and then coding a separate schema just to evaluate incoming and outgoing data. Finally, the doc functions could be used as a basis for unit/integration tests to ensure that all the requirements for the data have been met.


## Characteristics

### Engine Behavior

Integration of session / query with table classes.

Just as with Flask-SQLAlchemy, the `db` object carries a lot of the SQLAlchemy functionality. The `db` object has session as well as the other standard SQLAlchemy features.

### Model Behavior
#### Model Creation

Below is typical example of a table class with `dbbase`. Like Flask-SQLAlchemy, the models are created with db.Model that is an enhanced version of SQLAlchemy's declarative base.

```python
    class Job(db.Model):
        __tablename__ = 'jobs'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        another_id = db.Column(db.SmallInteger)
        start_date = db.Column(db.Date, default=date.today)
        update_at = db.Column(db.DateTime, onupdate=datetime.now)
        completed_at = db.Column(db.DateTime)
        completion_status = db.Column(db.SmallInteger, default=0)

```
#### Record Creation

Record creation uses the standard methods.

```python
    job = Job(
        name='model build process',
        another_id=4
        # letting defaults through
    )

    db.session.add(job)
    db.session.commit()

    # alternatively
    job.save()

```

#### Queries

The Model class also holds the query object.

Using SQLAlchemy, you would have a session object and do something along the lines of:

```python
    session.query(Job).filter(Job.start_date > '2020-04-01').all()
```
With Flask-SQLAlchemy and dbbase you would do:

```python
    Job.query.filter(Job.start_date > '2020-04-01').all()

```

#### Serialization

To accommodate differing formatting standards between JavaScript and Python when outputting JSON formatted data, the following conversion is available.

Start with a record:

```python

job = Job(
    id=123303,
    name='model build process',
    another_id=4,
    start_date='2020-04-15',
    update_at=datetime.datetime(2020, 4, 20, 3, 2, 1)
    completed_at = datetime.date(2020, 4, 30)
    completion_status = 0
).save()

job.serialize()

{
    "id": 123303,
    "name": "model build process",
    "anotherId": 4,
    "startDate": "2020-04-15",
    "updateAt": "2020-04-20 03:02:01"
    "endDate" = "2020-4-30"
    "completionStatus" = 0
}

```
Or, `job.serialize(to_camel_case=False)` would output it without any camel case conversion.

Incoming data could also be formatted as serialized above, and deserialied
via
```python
    Job.deserialize(data, from_camel_case=True)
```
Note that this does not update the record directly (the job in this example). Rather, the output is in the form of a dict. This gives an opportunity to evaluate the data prior to updating the record and database.

For example, suppose you also use `parser = reqparse.RequestParser()` from
Flask-Restful on the Flask side of things:

```python
    data = Job.deserialize(
        JobResource.parser.parse_args())
    job = Job(id, **data)
```

Finally, the serialize / deserialize functions can always be subclassed for special requirements of that particular model.

### Document Dictionaries

The same model, Job, can be expressed with details similarly to the OpenAPI specification for objects. It is a little different because SQLAlchemy has a more nuanced approach to defaults and onupdate functions, and foreign keys. Just as serialization mentioned above of objects can control what columns to include, the documentation function, `db.doc_table` enables control of what fields to include and what column properties to include.

The following command
```python
    db.doc_table(Job, to_camel_case=True, serial_fields=None, column_props=None)

```
produces this output.

```json
{
    "Job": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "format": "int32",
                "primary_key": true,
                "nullable": false,
                "info": {}
            },
            "name": {
                "type": "string",
                "nullable": false,
                "info": {}
            },
            "anotherId": {
                "type": "integer",
                "format": "int8",
                "nullable": true,
                "info": {}
            },
            "startDate": {
                "type": "date",
                "nullable": true,
                "default": {
                    "for_update": false,
                    "arg": "date.today"
                },
                "info": {}
            },
            "updateAt": {
                "type": "date-time",
                "nullable": true,
                "onupdate": {
                    "for_update": true,
                    "arg": "datetime.now"
                },
                "info": {}
            },
            "completedAt": {
                "type": "date-time",
                "nullable": true,
                "info": {}
            },
            "completionStatus": {
                "type": "integer",
                "format": "int8",
                "nullable": true,
                "default": {
                    "for_update": false,
                    "arg": 0
                },
                "info": {}
            }
        },
        "xml": "Job"
    }
}
```


## More

Additional documentation can be found at https://sidorof.github.io/dbbase/


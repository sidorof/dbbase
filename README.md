# dbbase

## Motivation

When starting out with Python long ago, the accepted method of interacting with PostgreSQL involved `psycopg` and some method of defining classes that represented table objects. To that end I created objects that could save, load, and interact with the database. From a design standpoint, this seemed natural and effective.

Then, SQLAlchemy came on the scene with its layer of abstraction. The design of table objects entailed a clear separation between table (model) objects and the connection to the database in the form of a session object. Moving with the times, I created a body of code organized around that principle and carted around the session object anytime I needed to interact with the database.

When using Flask and Flask-SQLAlchemy, the design pattern returned to the session object being once again integrated into the model object.

SQLAlchemy models outside of Flask can be shoehorned into the app, but we are left with the uneasy tension of interacting with the models in a different way.

One way to get around this would be to not use Flask-SQLAlchemy at all and roll-your-own within the context of Flask. Another way could be to use Flask-SQLAlchemy in programs that have nothing to do with Flask and accept carrying the baggage of Flask in applications that are isolated from the server.

This package implements a light-weight integration of a prototypical Model class with the session object and using a db object similarly to Flask-SQLAlchemy. The result of this tack is that the same interactions with the database can be applied whether the program is within the Flask environment or not.

## Goals

### Engine Behavior

* Integration of session with table objects

Just as with Flask-SQLAlchemy, the `db` object carries a lot of the SQLAlchemy functionality. In this case, the `db` object also has session as well as the other standard SQLAlchemy features.

### Model Behavior
* Model Creation

Below is typical example of a table class.
```
    class Job(db.Model):
        __tablename__ = 'jobs'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        another_id = db.Column(db.SmallInteger)
        start_date = db.Column(db.Date, default=date.today)
        update_time = db.Column(db.DateTime, default=datetime.now)
        end_date = db.Column(db.Date)
```
* Record Creation

Record creation uses the standard methods.
```
    job = Job(
        name='model build process',
        another_id=4
        # letting defaults for start_date and update_time through
    )

    db.session.add(job)
    db.session.commit()

```
* Queries

The model class also holds the query class.

Using SQLAlchemy, you would have a session object and do something along the
lines of:
```
session.query(Job).filter(Job.startdate > '2020-04-01').all()
```
With Flask-SQLAlchemy and dbbase you would do:
```
Job.query.filter(Job.startdate > '2020-04-01').all()

```
* JSON -- dicts

To accommodate differing formatting standards between JavaScript and Python when outputting JSON formatted data, the following conversion is available.

Start with a record:
```
    job = Job(
        id=123303,
        name='model build process,
        another_id=4,
        start_date='2020-04-15',
        update_time=datetime.datetime(2020, 4, 20, 3, 2, 1)
        end_date = datetime.date(2020, 4, 30)
)
job.serialize()

{
    "id": 123303,
    "name": "model build process",
    "anotherId": 4,
    "startDate": "2020-04-15",
    "updateTime": "2020-04-20 03:02:01"
    "endDate" = "2020-4-30"
}

```
Or, `job.serialize(js_xlate=False)` would output it without any conversion.

Incoming data could also be formatted as serialized above, and deserialied
via
```
Job.deserialize(data, js_xlate=True)
```
Note that this does not update the record directly (the job in this example). Rather, the output is in the form of a dict. This gives an opportunity evaluate the data prior to updating the record and database.

For example, suppose you also use `parser = reqparse.RequestParser()` from
flask_restful on the flask side of things:
```
data = Job.deserialize(
    JobResource.parser.parse_args())
job = Job(id, **data)
```
Finally, the serialize / deserialize functions can always be subclassed for special requirements of that particular model.


* Save  -- will have a function
* Delete -- will have a function
```

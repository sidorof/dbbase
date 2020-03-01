# dbbase

## Motivation

When starting out with Python long ago, the accepted method of interacting with PostgreSQL involved `psycopg` and some method of defining classes that represented table objects. To that end I created objects that could save, load, and interact with the database. From a design standpoint, this seemed natural and effective.

Then, SQLAlchemy came on the scene with its layer of abstraction. The design of table objects entailed a clear separation between table (model) objects and the connection to the database in the form of a session object. Moving with the times, I created a body of code organized around that principle and carted around the session object anytime I needed to interact with the database.

When using Flask and Flask-SQLAlchemy, the design pattern returned to the session object being once again integrated into the model object.

SQLAlchemy models outside of Flask can be shoehorned into the app, but we are left with the uneasy tension of interacting with the models in a different way.

One way to get around this would be to not use Flask-SQLAlchemy at all and roll-your-own within the context of Flask. Another way could be to use Flask-SQLAlchemy in programs that have nothing to do with Flask and accept carrying the baggage of Flask in applications that are isolated with the server.

The approach with this repository entails a light-weight integration of a prototypical model class with the session object and using a db object similarly to Flask-SQLAlchemy. The result of this tack is that the same interactions with the database can be applied whether the program is within the Flask environment or not.

## Goals

### Engine Behavior

* Integration of session with table objects


### Model Behavior

* Queries
* JSON -- dicts
* Save
* Delete

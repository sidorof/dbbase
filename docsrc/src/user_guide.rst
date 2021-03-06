==========
User Guide
==========

**DBBase** is a base implementation for creating SQLAlchemy models in a similar fashion to Flask-SQLAlchemy, but for use outside of the Flask environment. By using this it provides continuity to the code base, and maintains some the design advantages that Flask-SQLAlchemy implements.

**DBBase** also embodies default serialization / deserialization services as part of the Model class to cut down on total coding. Since much of the purpose of serialization is the creation of JSON objects that are to be used by JavaScript, it also can automatically convert the keys to camelCase (and back) as well.

------------
Introduction
------------

SQLAlchemy's design implements a clear separation between the session object, connections to a database, and the table definitions, the model. With such a separation, normal database usage involves carrying the session object into each program or function and combining it with the table class model for the appropriate actions.

Flask-SQLAlchemy uses SQLAlchemy, but provides an alternate approach to the design by embodying the session object into a primary database object (usually **db**), and suffusing the query into the table models as well. By doing so, many of the tools for interacting with the database are present and available within a table class.

**DBBase** maintains some continuity with the Flask-SQLAlchemy coding style.

--------------------
Database Connections
--------------------

Connecting to a database can be done as follows:

.. code-block:: python

    from dbbase import DB

    db = DB(config, model_class=None, checkfirst=True, echo=False)

..

The config is the database URI. There is a convenience function,
**db_config** that can help configure this URI. For example:

.. code-block:: python

    from dbbase import DB, db_config

    config = db_config(
        base="postgresql://{user}:{pass}@{host}:{port}/{dbname}",
        config_vars={
            'user': 'auser',
            'pass': '123',
            'host': 'localhost',
            'port': 5432,
            'dbname': 'mydatadb'
        }
    )

    db = DB(config=config, checkfirst=True, echo=False)

    # create any tables that are new, create a session object
    #   that is found at db.session
    db.create_all()
..

**db_config** just combines a base string with dict of variables,
resulting in a string that is fed into DB to configure the connection. So it can be complicated if necessary, but probably will not have to be.

**model_class** can substitute a different Model than this package,
but it is expected that normally the default would suffice.

**checkfirst** if True, will not recreate a table if it already
exists in the database.

**echo** if True logs the database interactions.

Unlike Flask-SQLAlchemy, DB does not default to an environment
variable `SQLALCHEMY_DATABASE_URI`. However, you could still use
it by extracting it from the environment and feeding it into DB.

------------------
Model Interactions
------------------

The following code compares typical table definition styles:

.. code-block:: python

    # SQLAlchemy
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String(30), nullable=False)
        addresses = relationship(
            "Address", backref="user", lazy='immediate')

    # Flask-SQLAlchemy
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(30), nullable=False)
        addresses = db.relationship(
            "Address", backref="user", lazy='immediate')

    # DBBase
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(30), nullable=False)
        addresses = db.relationship(
            "Address", backref="user", lazy='immediate')
..

Now if the only difference is a standard as to whether to explicitly import Column, and other classes, or have it ride around on db, no one would care.

The differences can be seen when interacting with the database. There is a ready conduit to the database within each class. For example, below shows filtering under all three scenarios.

.. code-block:: python

  # SQLAlchemy
  qry = session.query(User).filter_by(name='Bob').all()

  # Flask-SQLAlchemy
  qry = User.query.filter_by(name='Bob').all()

  # DBBase
  qry = User.query.filter_by(name='Bob').all()

..

The query object is conveniently available for use in the Model class.

First, we will create a user:

.. code-block:: python

  # both Flask-SQLAlchemy and DBBase
  user = User(name='Bob')
  db.session.add(user)
  db.session.commit()
..

**DBBase** also has a reference for convenience to the **db** variable within the Model class and the object instance.

.. code-block:: python

  # or DBBase via Model class
  user = User(name='Bob')
  User.db.session.add(user)
  User.db.session.commit()

  # or instance object
  user = User(name='Bob')
  user.db.session.add(user)
  user.db.session.commit()
..

Or, saving can be done via:

.. code-block:: python

  # DBBase
  user = User(name='Bob')
  User.save()

  # or even shorter
  user = User(name='Bob').save()
..

Deletion can also be done via the instance.

.. code-block:: python

  # DBBase
  user = User(name='Bob')
  User.save()

  # then delete
  user.delete()
..


-----------------
Record Validation
-----------------

A minor check can be performed prior to saving a record to ensure that all required fields have values. If there are any default values for the table, those will be ignored, but otherwise you can get a quick list of required columns without values.

.. code-block:: python

    status, errors = self.validate_record()
    if status:
        self.save()
    else:
        return errors
..

Suppose you have a user table with required first and last names. A user is created, but for some reason the last name is not filled in.

.. code-block:: python

    status, errors = user.validate_record()

    >> False, {"missing_values": ["last_name"]}
..

For consistency when communicating from an API to a front end application, a conversion to camel case can be done as well.


.. code-block:: python

    status, errors = user.validate_record(camel_case=True)

    >> False, {"missingValues": ["lastName"]}
..


Caveat

**DBBase** objects provide access to the SQLAlchemy **query** object, not the Flask-SQLAlchemy **query** object. Therefore you would not expect `User.query.get_or_404` to be available.

-------------
Serialization
-------------
For convenience building RESTful APIs, a default serialization function is
available for outputting JSON style strings. In addition, by default it converts the
keys to camelCase style to correspond to JavaScript conventions.

To illustrate some of the features, we will look at two examples: The first will be two tables, one for users and one for addresses

After the initial import and **db** creation, we create two tables.
The users table has a relationship with addresses where the user_id entered into the address table must be found in the users table.

As an aside, note that the password column is a `WriteOnlyColumn` for discussion later.

.. code-block:: python

    # create db that is sqlite in memory
    from dbbase import DB
    db = DB(config=':memory:')

    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(50), nullable=False)
        last_name =  db.Column(db.String(50), nullable=False)
        password = db.WriteOnlyColumn(db.String, nullable=False)
        addresses = db.relationship(
            "Address", backref="user", lazy='immediate')

    def full_name(self):
        return '{first} {last}'.format(
            first=self.first_name, last=self.last_name)

    class Address(db.Model):
        __tablename__ = 'addresses'
        id = db.Column(db.Integer, primary_key=True)
        email_address = db.Column(db.String, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    db.create_all()

    user = User(first_name='Bob', last_name='Smith')

    user.save()

    address1 = Address(
        email_address='email1@example.com',
        user_id=user.id
    )
    address2 = Address(
        email_address='email2@example.com',
        user_id=user.id
    )

    db.session.add(address1)
    db.session.add(address2)
    db.session.commit()
..

Accordingly, it makes sense that when the user data is to be pulled from an API the relevant addresses be included.

.. code-block:: python

   >>> print(user.serialize(indent=2))

   {
     "addresses": [
       {
         "userId": 3,
         "emailAddress": "email1@example.com",
         "id": 1
       },
       {
         "userId": 3,
         "emailAddress": "email2@example.com",
         "id": 2
       }
     ],
     "lastName": "Smith",
     "fullName": "Bob Smith",
     "id": 3,
     "firstName": "Bob"
   }
..

The default serialization opts for the keys to be put into camelCase. In addition, it walks the object dictionary and recursively evaluates any relationships as well, under the assumption that it would minimize the number of trips to the API from the front end.

WriteOnlyColumn
===============

The user table above includes a password column using a `db.WriteOnlyColumn`. By using this type of column, a table can automatically exclude that column from serialization once the value has been filled in. This avoids an awkward mistake accidentally outputting even an encrypted password, yet including the field when None for forms to a front-end application adding a new user.

Controlling Serialization
=========================

You have the ability to limit or expand the items that are included.

* **SERIAL_STOPLIST** is a Model class variable that is a list of fields to ignore

* **SERIAL_FIELDS** is a Model class variable that is a list of fields that would be included. Additional methods can be included in this list to enable fields like **fullname** in place of **first_name** and **last_name**.

* **SERIAL_FIELD_RELATIONS** is a Model class variable that is a dictionary. With this variable you can specify what fields a relation will show. While you could go to the table definition for that relation and specify it directly, using the SERIAL_FIELD_RELATIONS variable enables you to show the specific fields appropriate for when that relationship is included with the current table, but have a standard method when show the relation table directly. An example below will help explain that further.

* **serialize** of course can be overwritten in your class model so if either method is not right for your situation it is easy enough to set right for that particular class yet use the defaults for other tables.

To reduce ambiguity, if **SERIAL_FIELDS** is used, serialization
assumes that the list is explicitly what you want, and ignores the **SERIAL_STOPLIST**.

From examining the output that we have above, suppose we decide that we will just present the full name and not **first_name** and **last_name**.

In that case would do the following:

.. code-block:: python

    class User(db.Model):
        __tablename__ = 'users'
        SERIAL_STOPLIST = ['first_name', 'last_name']

        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(50), nullable=False)
        last_name =  db.Column(db.String(50), nullable=False)
        addresses = db.relationship(
            "Address", backref="user", lazy='immediate')

    def full_name(self):
        return '{first} {last}'.format(
            first=self.first_name, last=self.last_name)
..

Now when we run **serialize**, the fields first_name and last_name are filtered out.

.. code-block:: python

    >>> print(user.serialize(indent=2))

    {
      "addresses": [
        {
          "userId": 3,
          "emailAddress": "email1@example.com",
          "id": 1
        },
        {
          "userId": 3,
          "emailAddress": "email2@example.com",
          "id": 2
        }
      ],
      "id": 3,
      "fullName": "Bob Smith"
    }
..

Now since **user_id** in addresses is redundant, we can also filter that out. Let us remove **id** from addresses as well. We could do
this by adding both to a stop list by:

.. code-block:: python

    Address.SERIAL_STOPLIST = ['id', 'user_id']
..

But instead, we can minimize our typing by instead adding just the email address to **SERIAL_FIELDS**. As in the following:

.. code-block:: python

    class Address(db.Model):
        __tablename__ = 'addresses'
        SERIAL_FIELDS = ['email_address']

        id = db.Column(db.Integer, primary_key=True)
        email_address = db.Column(db.String, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
..

Running **user.serialize()** again we have a more compact result

.. code-block:: python

    >>> print(user.serialize(indent=2))
    {
      "addresses": [
        {
          "emailAddress": "email1@example.com"
        },
        {
          "emailAddress": "email2@example.com"
        }
      ],
      "id": 3,
      "fullName": "Bob Smith"
    }
..

Dictionary keys have not been guaranteed to print in a particular
order, although that is changing. If the order of the keys in
serialization are important in your application, you can control
that by putting those variables in **SERIAL_FIELDS**.

.. code-block:: python

    User.SERIAL_FIELDS = ['id', 'first_name', 'last_name', 'addresses']

    >>> print(user.serialize(indent=2))
    {
      "id": 3,
      "firstName": "Bob",
      "lastName": "Smith",
      "addresses": [
        {
          "userId": 3,
          "emailAddress": "email1@example.com",
          "id": 1
        },
        {
          "userId": 3,
          "emailAddress": "email2@example.com",
          "id": 2
        }
      ]
    }
..

Example of SERIAL_FIELD_RELATIONS

In the example above we controlled the output for Address by using `Address.SERIAL_FIELDS = ['email_address']`. That means that any time an API would call for an addres only the email address would be returned. If it is **only** going to be returned in conjunction with a user, that may be acceptable. However, there are many secondary relationships where more control would be helpful.

In the following code block we will see our tables created again, but with the use of the SERIAL_FIELD_RELATIONS variable to help us to a more refined output.

.. code-block:: python

    class User(db.Model):
        __tablename__ = 'users'
        SERIAL_STOPLIST = ['first_name', 'last_name']
        SERIAL_FIELD_RELATIONS = {
            "Address": ["id", "email_address"]
        }

        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(50), nullable=False)
        last_name =  db.Column(db.String(50), nullable=False)
        addresses = db.relationship(
            "Address", backref="user", lazy='immediate')

    def full_name(self):
        return '{first} {last}'.format(
            first=self.first_name, last=self.last_name)


    class Address(db.Model):
        __tablename__ = 'addresses'

        id = db.Column(db.Integer, primary_key=True)
        email_address = db.Column(db.String, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


    >>> print(user.serialize(indent=2))
    {
      "id": 3,
      "firstName": "Bob",
      "lastName": "Smith",
      "addresses": [
        {
          "emailAddress": "email1@example.com",
          "id": 1
        },
        {
          "emailAddress": "email2@example.com",
          "id": 2
        }
      ]
    }

..

When a field is found to be an instance of a class that is a key in the `SERIAL_FIELD_RELATIONS` dictionary, the corresponding list is used for that class in place of the default class.


Ad Hoc Variables

Both the `serialize` and `to_dict` functions have parameters of `serial_fields` and `serial_field_relations`. If not used, the default class variables are
used. However, with these variables, you can generate custom serializations on the fly to better match specific requirements.

A natural fall-out of this approach means also that such things as views can be easily created for different audiences.


Recursive Serialization
=======================

For this next section, let us start by first revoking the stop lists and serial lists that we have and take a look at the process in a different way.

.. code-block:: python

    # assume the class variables are set on the defaults in their class definitions.
    User.SERIAL_FIELDS = None
    User.SERIAL_STOPLIST = None
    User.SERIAL_FIELD_RELATIONS = None

    Address.SERIAL_FIELDS = None
    Address.SERIAL_STOPLIST = None
    Address.SERIAL_FIELD_RELATIONS = None

    >>> print(user.serialize(indent=2))
    {
      "addresses": [
        {
          "userId": 3,
          "emailAddress": "email1@example.com",
          "id": 1
        },
        {
          "userId": 3,
          "emailAddress": "email2@example.com",
          "id": 2
        }
      ],
      "lastName": "Smith",
      "fullName": "Bob Smith",
      "id": 3,
      "firstName": "Bob"
    }
..

As a note, if you change such class variables on the fly such as User.SERIAL_FIELDS, you might well have unintended effects.

See how the address serialization digs back into the user object. This is due to the relationship that Address has with User. But, serializatin does not go back to User once again when you run **user.serialize()**. The reason is that are there are limits in place to avoid going into an endless loop.

However, there are situations where it is entirely desirable.

We now create a table for holding network nodes. A node can be connected to other nodes in a relationship to form tree structures for example. Because of that, the relationships are self-referential. Where in the example above, we needed to stop serialization before it turns back in on itself, now we want to follow the relationships all the way down.

To show this we first create the table and a few nodes, and connect them together. Let's model
.. code-block::

                    node 1
                    |    |
                node 2   node 5
                |    |        |
            node 3   node 4   node 6

..


.. code-block:: python

    class Node(db.Model):
        """self-referential table"""
        __tablename__ = 'nodes'
        id = db.Column(db.Integer, primary_key=True)
        parent_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
        data = db.Column(db.String(50))
        children = db.relationship(
            "Node",
            lazy="joined",
            order_by="Node.id",
            join_depth=10)

        SERIAL_FIELDS = ['id', 'parent_id', 'data', 'children']

    db.create_all()

    node1 = Node(id=1, data='this is node1')
    node2 = Node(id=2, data='this is node2')
    node3 = Node(id=3, data='this is node3')
    node4 = Node(id=4, data='this is node4')
    node5 = Node(id=5, data='this is node5')
    node6 = Node(id=6, data='this is node6')

    db.session.add(node1)
    db.session.commit()
    node1.children.append(node2)
    db.session.commit()
    node2.children.append(node3)
    db.session.commit()
    node2.children.append(node4)
    db.session.commit()
    node1.children.append(node5)
    db.session.commit()
    node5.children.append(node6)
    db.session.commit()
..

So the nodes are all linked up with node1 as the root. So when we serialize node 1 we get:

.. code-block:: python

    >>> node1.serialize(indent=2)
    {
      "id": 1,
      "parentId": null,
      "data": "this is node1",
      "children": [
        {
          "id": 2,
          "parentId": 1,
          "data": "this is node2",
          "children": [
            {
              "id": 3,
              "parentId": 2,
              "data": "this is node3",
              "children": []
            },
            {
              "id": 4,
              "parentId": 2,
              "data": "this is node4",
              "children": []
            }
          ]
        },
        {
          "id": 5,
          "parentId": 1,
          "data": "this is node5",
          "children": [
            {
              "id": 6,
              "parentId": 5,
              "data": "this is node6",
              "children": []
            }
          ]
        }
      ]
    }
..

By the way, showing examples of serialization in printed form is much better if the JSON version is indented. In fact, the default is the more compact form to reduce overall size of the output. For example, the above emitted from an API would be:

.. code-block:: python

    >>> node1.serialize()
..

{"id": 1, "parentId": null, "data": "this is node1", "children": [{"id": 2, "parentId": 1, "data": "this is node2", "children": [{"id": 3, "parentId": 2, "data": "this is node3", "children": []}, {"id": 4, "parentId": 2, "data": "this is node4", "children": []}]}, {"id": 5, "parentId": 1, "data": "this is node5", "children": [{"id": 6, "parentId": 5, "data": "this is node6", "children": []}]}]}


---------------------
Document Dictionaries
---------------------

Document Dictionaries introspect the model classes you have built and present the data objects in a format similar to Swagger / OpenAPI. This enables a method for communicating the details of the models. In addition, the functions could be wrapped into parsing functions that evaluate query strings and form data, directly from the table characteristics. This avoids the extra work of defining tables, and then coding a separate schema just to evaluate incoming and outgoing data. Finally, the doc functions could be used as a basis for unit/integration tests to ensure that all the requirements for the data have been met.

Table Documentation
===================

Suppose we were to describe the two tables created above, User, and Address.

.. code-block:: python

    >>> db.doc_tables(to_camel_case=True)

..

This would yield the following output that details object models similarly to OpenApi. It details the column characteristics for each table. Note how the foreign key is annotated in Address. If defaults had been defined for the tables, it would detail the default type including server defaults.

In the example shown, the column names have been converted to camel case. Front end developers, used to JavaScript notation may be more comfortable in this format.


.. code-block:: json

    {
        "definitions": {
            "Address": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "format": "int32",
                        "primary_key": true,
                        "nullable": false,
                        "info": {}
                    },
                    "email_address": {
                        "type": "string",
                        "nullable": false,
                        "info": {}
                    },
                    "user_id": {
                        "type": "integer",
                        "format": "int32",
                        "nullable": true,
                        "foreign_key": "users.id",
                        "info": {}
                    },
                    "user": {
                        "readOnly": false,
                        "relationship": {
                            "type": "single",
                            "entity": "User",
                            "fields": {
                                "id": {
                                    "type": "integer",
                                    "format": "int32",
                                    "primary_key": true,
                                    "nullable": false,
                                    "info": {}
                                },
                                "full_name": {
                                    "readOnly": true
                                }
                            }
                        }
                    }
                },
                "xml": "Address"
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "format": "int32",
                        "primary_key": true,
                        "nullable": false,
                        "info": {}
                    },
                    "addresses": {
                        "readOnly": false,
                        "relationship": {
                            "type": "list",
                            "entity": "Address",
                            "fields": {
                                "id": {
                                    "type": "integer",
                                    "format": "int32",
                                    "primary_key": true,
                                    "nullable": false,
                                    "info": {}
                                },
                                "email_address": {
                                    "type": "string",
                                    "nullable": false,
                                    "info": {}
                                },
                                "user_id": {
                                    "type": "integer",
                                    "format": "int32",
                                    "nullable": true,
                                    "foreign_key": "users.id",
                                    "info": {}
                                }
                            }
                        }
                    },
                    "full_name": {
                        "readOnly": true
                    }
                },
                "xml": "User"
            }
        }
    }
..

Filtering for Form Data and Query Strings
=========================================

If you have used Flask-Restful, one of the features involves argument parsing of form data, query strings, etc. This involves entering arguments such as:

.. code-block:: python

    parser = reqparse.RequestParser()
    parser.add_argument("id", type=int, required=False)
    parser.add_argument("firstName", type=str, required=True)
    parser.add_argument("lastName", type=str, required=True)

..

The kind of characteristics necessary to process that data is already available from the above objects. The creators of Flask-Restful have indicated that they are going to eventually drop support of the `reqparse` class would does the above.

Using generated objects such as above can be wrapped into a parsing mechanism reducing the need for a duplication of effort. You have already done the work of carefully crafting your tables. Using the document dictionaries you can get more mileage out of it.

A Larger Example of a Document Dictionary
=========================================

To get an idea of the range of support it helps to see a more complicated table. The following table is basically a zoo of different combinations of column types and parameters.

.. code-block:: python

       status_codes = [
            [0, "New"],
            [1, "Active"],
            [2, "Suspended"],
            [3, "Inactive"],
        ]

        class StatusCodes(types.TypeDecorator):
            """
            Status codes are entered as strings and converted to
            integers when saved to the database.
            """
            impl = types.Integer

            def __init__(self, status_codes, **kw):
                self.choices = dict(status_codes)
                super(StatusCodes, self).__init__(**kw)

            def process_bind_param(self, value, dialect):
                """called when saving to the database"""
                return [
                    k
                    for k, v in self.choices.items()
                    if v == value
                ][0]

            def process_result_value(self, value, dialect):
                """called when pulling from database"""
                return self.choices[value]

        class BigTable(db.Model):
            """Test class with a variety of column types"""
            __tablename__ = "main"

            id = db.Column(
                db.Integer,
                primary_key=True,
                nullable=True,
                comment="Primary key with a value assigned by the database",
                info={"extra": "info here"},
            )

            status_id = db.Column(
                StatusCodes(status_codes),
                nullable=False,
                comment="Choices from a list. String descriptors "
                "change to integer upon saving. Enums without the headache.",
            )

            @db.orm.validates("status_id")
            def _validate_id(self, key, id):
                """_validate_id

                Args:
                    id: (int) : id must be in cls.choices
                """
                if id not in dict(status_codes):
                    raise ValueError("{} is not valid".format(id))
                return id

            # nullable / not nullable
            name1 = db.Column(
                db.String(50), nullable=False, comment="This field is required"
            )
            name2 = db.Column(
                db.String(50),
                nullable=True,
                comment="This field is not required",
            )

            # text default
            name3 = db.Column(
                db.Text,
                default="test",
                nullable=False,
                comment="This field has a default value",
                index=True,
            )

            item_length = db.Column(
                db.Float, nullable=False, comment="This field is a float value"
            )

            item_amount = db.Column(db.Numeric(17, 6), default=0.0)

            # integer and default
            some_small_int = db.Column(
                db.SmallInteger,
                default=0,
                nullable=False,
                comment="This field is a small integer",
            )
            some_int = db.Column(
                db.Integer,
                default=0,
                nullable=False,
                comment="This field is a 32 bit integer",
            )
            some_big_int = db.Column(
                db.BigInteger,
                default=0,
                nullable=False,
                comment="This field is a big integer",
            )

            fk_id = db.Column(
                db.Integer,
                db.ForeignKey("other_table.id"),
                nullable=False,
                comment="This field is constrained by a foreign key on"
                "another table",
            )

            today = db.Column(
                db.Date,
                doc="this is a test",
                info={"test": "this is"},
                comment="This field defaults to today, created at model level",
                default=date.today,
            )

            created_at1 = db.Column(
                db.DateTime,
                default=datetime.now,
                comment="This field defaults to now, created at model level",
            )
            created_at2 = db.Column(
                db.DateTime,
                server_default=db.func.now(),
                comment="This field defaults to now, created at the server"
                "level",
            )
            update_time1 = db.Column(
                db.DateTime,
                onupdate=datetime.now,
                comment="This field defaults only on updates",
            )
            update_time2 = db.Column(
                db.DateTime,
                server_onupdate=db.func.now(),
                comment="This field defaults only on updates, but on the"
                "server",
            )

            unique_col = db.Column(
                db.String(20),
                unique=True,
                comment="This must be a unique value in the database.",
            )

            # adapted from sqlalchemy docs
            abc = db.Column(
                db.String(20),
                server_default="abc",
                comment="This field defaults to text but on the server.",
            )
            index_value = db.Column(
                db.Integer,
                server_default=db.text("0"),
                comment="This field defaults to an integer on the server.",
            )

            __table_args = (
                db.Index("ix_name1_name2", "name1", "name2", unique=True),
            )

        class OtherTable(db.Model):
            __tablename__ = "other_table"
            id = db.Column(db.Integer, primary_key=True, nullable=True)

 ..

From that table we can generation our document dictionary:

.. code-block:: json

    {
        "BigTable": {
            "type": "object",
            "properties": {
                "item_amount": {
                    "type": "numeric(17, 6)",
                    "nullable": true,
                    "default": {
                        "for_update": false,
                        "arg": 0.0
                    },
                    "info": {}
                },
                "name2": {
                    "type": "string",
                    "maxLength": 50,
                    "nullable": true,
                    "comment": "This field is not required",
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
                "fk_id": {
                    "type": "integer",
                    "format": "int32",
                    "nullable": false,
                    "foreign_key": "other_table.id",
                    "comment": "This field is constrained by a foreign key onanother table",
                    "info": {}
                },
                "some_small_int": {
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
                "some_int": {
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
                "update_time2": {
                    "type": "date-time",
                    "nullable": true,
                    "server_onupdate": {
                        "for_update": true,
                        "arg": "db.func.now()",
                        "reflected": false
                    },
                    "comment": "This field defaults only on updates, but on theserver",
                    "info": {}
                },
                "index_value": {
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
                "update_time1": {
                    "type": "date-time",
                    "nullable": true,
                    "onupdate": {
                        "for_update": true,
                        "arg": "datetime.now"
                    },
                    "comment": "This field defaults only on updates",
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
                "created_at1": {
                    "type": "date-time",
                    "nullable": true,
                    "default": {
                        "for_update": false,
                        "arg": "datetime.now"
                    },
                    "comment": "This field defaults to now, created at model level",
                    "info": {}
                },
                "name1": {
                    "type": "string",
                    "maxLength": 50,
                    "nullable": false,
                    "comment": "This field is required",
                    "info": {}
                },
                "created_at2": {
                    "type": "date-time",
                    "nullable": true,
                    "server_default": {
                        "for_update": false,
                        "arg": "db.func.now()",
                        "reflected": false
                    },
                    "comment": "This field defaults to now, created at the serverlevel",
                    "info": {}
                },
                "some_big_int": {
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
                "unique_col": {
                    "type": "string",
                    "maxLength": 20,
                    "nullable": true,
                    "unique": true,
                    "comment": "This must be a unique value in the database.",
                    "info": {}
                },
                "item_length": {
                    "type": "float",
                    "nullable": false,
                    "comment": "This field is a float value",
                    "info": {}
                },
                "status_id": {
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
                }
            },
            "xml": "BigTable"
        }
    }

..

This output illustrates a range of some of what is available and how the parameters are formatted.

.. code-block:: yaml

  BigTable:
    type: object
    properties:
        abc:
            comment: This field defaults to text but on the server.
            info: {}
            maxLength: 20
            nullable: true
            server_default:
                arg: abc
                for_update: false
                reflected: false
            type: string
        created_at1:
            comment: This field defaults to now, created at model level
            default:
                arg: datetime.now
                for_update: false
            info: {}
            nullable: true
            type: date-time
        created_at2:
            comment: This field defaults to now, created at the serverlevel
            info: {}
            nullable: true
            server_default:
                arg: db.func.now()
                for_update: false
                reflected: false
            type: date-time
        fk_id:
            comment: This field is constrained by a foreign key onanother table
            foreign_key: other_table.id
            format: int32
            info: {}
            nullable: false
            type: integer
        id:
            comment: Primary key with a value assigned by the database
            format: int32
            info:
                extra: info here
            nullable: true
            primary_key: true
            type: integer
        index_value:
            comment: This field defaults to an integer on the server.
            format: int32
            info: {}
            nullable: true
            server_default:
                arg: db.text("0")
                for_update: false
                reflected: false
            type: integer
        item_amount:
            default:
                arg: 0.0
                for_update: false
            info: {}
            nullable: true
            type: numeric(17, 6)
        item_length:
            comment: This field is a float value
            info: {}
            nullable: false
            type: float
        name1:
            comment: This field is required
            info: {}
            maxLength: 50
            nullable: false
            type: string
        name2:
            comment: This field is not required
            info: {}
            maxLength: 50
            nullable: true
            type: string
        name3:
            comment: This field has a default value
            default:
                arg: test
                for_update: false
            index: true
            info: {}
            nullable: false
            type: text
        some_big_int:
            comment: This field is a big integer
            default:
                arg: 0
                for_update: false
            format: int64
            info: {}
            nullable: false
            type: integer
        some_int:
            comment: This field is a 32 bit integer
            default:
                arg: 0
                for_update: false
            format: int32
            info: {}
            nullable: false
            type: integer
        some_small_int:
            comment: This field is a small integer
            default:
                arg: 0
                for_update: false
            format: int8
            info: {}
            nullable: false
            type: integer
        status_id:
            choices:
                0: New
                1: Active
                2: Suspended
                3: Inactive
            comment: Choices from a list. String descriptors change to integer upon
                saving. Enums without the headache.
            format: int32
            info: {}
            nullable: false
            type: integer
        today:
            comment: This field defaults to today, created at model level
            default:
                arg: date.today
                for_update: false
            doc: this is a test
            info:
                test: this is
            nullable: true
            type: date
        unique_col:
            comment: This must be a unique value in the database.
            info: {}
            maxLength: 20
            nullable: true
            type: string
            unique: true
        update_time1:
            comment: This field defaults only on updates
            info: {}
            nullable: true
            onupdate:
                arg: datetime.now
                for_update: true
            type: date-time
        update_time2:
            comment: This field defaults only on updates, but on theserver
            info: {}
            nullable: true
            server_onupdate:
                arg: db.func.now()
                for_update: true
                reflected: false
            type: date-time
    xml: BigTable

..


**DBBase** is compatible with Python >=3.6 and is distributed under the
MIT license.

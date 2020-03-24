======
dbbase
======

**dbbase** is a base implementation for creating SQLAlchemy models in a similar fashion to Flask-SQLAlchemy, but for use outside of the Flask environment. By using this it provides continuity to the code base, and maintains some the design advantages that Flask-SQLAlchemy implements.

**dbbase** also embodies default serialization / deserialization services as part of the Model class to cut down on total coding. Since much of the purpose of serialization is the creation of JSON objects that are to be used by JavaScript, it also can automatically convert the keys to camelCase (and back) as well.

------------
Introduction
------------

SQLAlchemy's design implements a clear separation between the session object, connections to a database, and the table definitions, the model. With such a separation, normal database usage involves carrying the session object into each program or function and combining it with the table class model for the appropriate actions.

Flask-SQLAlchemy uses SQLAlchemy, but provides an alternate approach to the design by embodying the session object into a primary database object (usually `db`), and suffusing the query into the table models as well. By doing so, many of the tools for interacting with the database are present and available within a table class.

dbbase maintains some continuity with Flask-SQLAlchemy coding style.

The following code compares a typical table definition styles:

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

    # dbbase
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
  qry = session.query(User).filter_by(name = 'Bob').all()

  # Flask-SQLAlchemy
  qry = User.query.filter_by(name = 'Bob').all()

  # dbbase
  qry = User.query.filter_by(name = 'Bob').all()

..

The query object is conveniently available for use in the Model class.

In addition, access to the session object is provided similarly:

.. code-block:: python

  # both Flask-SQLAlchemy and dbbase
  user = User(name='Bob')
  db.session.add(user)
  db.session.commit()
..

**dbbase** also has a reference for convenience to the `db` variable within the Model class or the object instance.

.. code-block:: python

  # or dbbase via Model class
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

  # dbbase
  user = User(name='Bob')
  User.save()

  # or even shorter
  user = User(name='Bob').save()
..

Caveat

**dbbase** objects provide access to the SQLAlchemy `query` object, not the Flask-SQLAlchemy `query` object. Therefore you would not expect `User.query.get_or_404` to be available.

-------------
Serialization
-------------
For convenience building RESTful APIs, a default serialization function is
available for outputting JSON style strings. In addition, by default it converts the
keys to camelCase style to correspond to JavaScript conventions.

To illustrate some of the features, we will look at two examples: The first will be two tables, one for users and one for addresses

After the initial import and `db` creation, we create two tables.
The users table has a relationship with addresses where the user_id entered into the address table must be found in the users table.

.. code-block:: python

    # create db that is sqlite in memory
    from dbbase import DB
    db = DB(config=':memory:')

    class User(db.Model):
        __tablename__ = 'users'
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

    db.create_all()

    user = User(first_name='Bob', last_name='Smith')

    db.session.add(user)
    db.session.commit()

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

   >>> print(user.serialize())
   {
     "firstName": "Bob",
     "fullName": "Bob Smith",
     "lastName": "Smith",
     "addresses": [
       {
         "emailAddress": "email1@example.com",
         "id": 1,
         "userId": 1
       },
       {
         "emailAddress": "email2@example.com",
         "id": 2,
         "userId": 1
       }
     ],
     "id": 1
   }

The default serialization opts for the keys to be put into camelCase. In addition, it walks the object dictionary and recursively evaluates any relationships as well under the assumption that it would minimize the number of trips to the API from the front end.

Controlling Serialization
=========================

You have the ability to limit or expand the items that are included.

* `SERIAL_STOPLIST` is a Model class variable that is a list of fields to ignore

* `SERIAL_LIST` is a Model class variable that is a list of fields that would be included. Additional methods can be included in this list to enable fields like `fullname` in place of `first_name` and `last_name`.

* `serialize` of course can be overwritten in your class model so if either method is not right for your situation it is easy enough to set right for that particular class yet use the defaults for other tables.

To reduce ambiguity, if `SERIAL_LIST` is used, serialization
assumes that the list is explicitly what you want. The object of
the game

From examining the output that we have above, suppose we decide that we will just present the full name and not `first_name` and `last_name`.

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

Now when we run `serialize`, the fields first_name and last_name are filtered out.

.. code-block:: python

    >>> print(user.serialize()

    {
        "id": 1,
        "addresses": [
            {
                "id": 1,
                "userId": 1,
                "emailAddress": "email1@example.com"
            },
            {
                "id": 2,
                "userId": 1,
                "emailAddress": "email2@example.com"
            }
        ],
        "fullName": "Bob Smith"
    }
..

Now since `user_id` in addresses is redundant, we can also filter that out. Let us remove `id` from addresses as well. We could do
this by adding both to a stop list by:

.. code-block:: python

    Address.SERIAL_STOPLIST = ['id', 'user_id']
..

But instead, we can minimize our typing by instead adding just the email address to `SERIAL_LIST`. As in the following:

.. code-block:: python

    class Address(db.Model):
        __tablename__ = 'addresses'
        SERIAL_LIST = ['id', 'user_id']

        id = db.Column(db.Integer, primary_key=True)
        email_address = db.Column(db.String, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
..

Running `user.serialize()` again we have a more compact result

.. code-block:: python

    >>> print(user.serialize())
    {
        "fullName": "Bob Smith",
        "id": 1,
        "addresses": [
            {
                "emailAddress": "email1@example.com"
            },
            {
                "emailAddress": "email2@example.com"
            }
        ]
    }
..

Recursive Serialization
=======================

For this next section, let us start by first revoking the stop lists and serial lists that we have and take a look at the process in a different way.

.. code-block:: python

    >>> User.SERIAL_LIST = None
    >>> User.SERIAL_STOPLIST = []

    >>> Address.SERIAL_LIST = None
    >>> Address.SERIAL_STOPLIST = []


    >>> print(user.serialize())
    {
        "firstName": "Bob",
        "id": 1,
        "fullName": "Bob Smith",
        "lastName": "Smith",
        "addresses": [
            {
                "emailAddress": "email1@example.com",
                "userId": 1,
                "id": 1
            },
            {
                "emailAddress": "email2@example.com",
                "userId": 1,
                "id": 2
            }
        ]
    }
..

So we can see that it is back to the original form. But lets choose `address1.serialize()`.

.. code-block:: python

    >>> print(address1.serialize())
    {
        "emailAddress": "email1@example.com",
        "userId": 1,
        "id": 1,
        "user": {
            "firstName": "Bob",
            "id": 1,
            "fullName": "Bob Smith",
            "lastName": "Smith"
        }
    }

..

See how the address serialization digs back into the user object. This is due to the relationship that Address has with User. But, serializatin does not go back to User once again when you run `user.serialize()`. The reason is that are there are limits in place to avoid going into an endless loop.

However, there are situations where it is entirely desirable.

We now create a table for holding network nodes. A node can be connected to other nodes in a relationship to form tree structures for example. Because of that, the relationships are self-referential. Where in the example above, we needed to stop serialization before it turns back in on itself, now we want to follow the relationships all the way down.

To show this we first create the table and a few nodes, and connect them together:

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

    >>> node1.serialize(indent=4)

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

**dbbase** is compatible with Python >=3.6 and is distributed under the
MIT license.

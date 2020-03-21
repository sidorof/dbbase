# dbbase/serializers.py
"""
This module implements serializations. Here are a couple scenarios:

Scenario 1:

Preparing the table and data

    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(30), nullable=False)


    class Address(db.Model):
        __tablename__ = 'addresses'
        id = db.Column(db.Integer, primary_key=True)
        email_address = db.Column(db.String, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

        user = db.relationship("User", back_populates="addresses")

    User.addresses = db.relationship(
        "Address", back_populates="user", lazy='immediate')

    User.metadata.create_all(db.session.bind)

    user = User(name='Bob')
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


Serializations:

    JSON in camel case should look like this:
    {
        "id": 1,
        "name": "Bob",
        "addresses": [
            {
            "userId": 1,       -- could conceivably be dropped
            "emailAddress": "email1@example.com",
            "id": 1
            },
            {
            "userId": 1,       -- could conceivably be dropped
            "emailAddress": "email2@example.com",
            "id": 2
            }
        ]
    }

    or this:
    {
        "id": 1,
        "name": "Bob",
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

    So serialization walks the object __dict__
"""
from datetime import date, datetime
from decimal import Decimal

from . import model


SA_INDICATOR = "_sa_instance_state"
DATE_FMT = "%F"
TIME_FMT = "%Y-%m-%d %H:%M:%S"
STOP_VALUE = "%%done%%"  # seems awkward

# fields automatically excluded
SERIAL_STOPLIST = [
    '_class',
    '_decl_class_registry',
    '_sa_class_manager',
    '_sa_instance_state',
    'db',
    'deserialize',
    'get_serial_field_list',
    'metadata',
    'query',
    'save',
    'serialize',
    'to_dict',
    'SERIAL_STOPLIST',
    'SERIAL_LIST'
]


def _eval_value(value, to_camel_case, level_limits, source_class):
    """ _eval_value

    This function converts some of the standard values as needed based
    upon type. The more complex values are farmed out, such as for lists
    and models.

    parameters:
        value
            what is to be evaluated and perhaps converted

        to_camel_case
            Boolean for converting keys to camel case

        level_limits
            set of classes that have been visited already
            it is to prevent infinite recursion situations
        source_class

    returns
        values that have been converted as needed
    """
    if isinstance(value, datetime):
        result = value.strftime(TIME_FMT)
    elif isinstance(value, date):
        result =  value.strftime(DATE_FMT)
    elif isinstance(value, Decimal):
        result =  str(value)
    elif isinstance(value, list):
        if len(value) > 0:
            result, level_limits = _eval_value_list(
                value, to_camel_case, level_limits, source_class)
        else:
            result = []
    elif hasattr(value, 'to_dict'):
        result, level_limits =  _eval_value_model(
            value, to_camel_case, level_limits, source_class
        )
    else:
        result =  value

    return result


def _eval_value_model(value, to_camel_case, level_limits, source_class):
    """_eval_value_model

    if any class within level_limits i self-referential it gets
    passed on.
    """
    result = STOP_VALUE
    status = True
    if source_class is not None:
        level_limits.add(source_class)
    result = value.to_dict(to_camel_case, level_limits=level_limits)
    level_limits.add(value._class())
    return result, level_limits


def _eval_value_list(value, to_camel_case, level_limits, source_class):
    """_eval_value_list

    This function handles values that are lists. While a list that is not
    a model is pretty straight-forward, a list of models is a little
    trickier.

    If a model is self-referential, such as a node, the model should be
    passed on to be evaluated. However, if it is not, such as
        user > addresses > user,
    then if the model has not already been evaluated, it should be.
    But, it should be for each line in the list, so you can't mark it as
    done until all the lines have been processed. The approach taken here is
    to make a temporary level_limits set, pass it in, but start it fresh
    for the next line. Only at the end should level_limits be updated.

    """
    tmp_list = []
    length = len(value)

    is_model = False
    tmp_limits = None
    for item in value:
        tmp_limits = level_limits.copy()
        if hasattr(item, 'to_dict'):
            status = True
            result = STOP_VALUE
            if item._class() in level_limits:
                if not item._has_self_ref():
                    status = False
            if status:
                result, tmp_limits = _eval_value_model(
                    item, to_camel_case, tmp_limits, source_class)
        else:
            result = _eval_value(
                item, to_camel_case, tmp_limits, source_class)

        tmp_list.append(result)

    if all(list(map(lambda i: i == STOP_VALUE, tmp_list))):
        tmp_list = STOP_VALUE
    if tmp_limits is not None:
        level_limits = tmp_limits.copy()

    return tmp_list, level_limits

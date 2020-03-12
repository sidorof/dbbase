# dbbase/serializers.py
"""
This module implements serializations. It is

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
        #"Address", order_by='Address.id', back_populates="user")

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

    JSON should look like:
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




"""
from datetime import date, datetime
from decimal import Decimal

from . import model


SA_INDICATOR = '_sa_instance_state'
DATE_FMT = '%F'
TIME_FMT = '%Y-%m-%d %H:%M:%S'
STOP_VALUE = '%%done%%'  # seems awkward


def _eval_value(value, class_name, to_camel_case, level_limits):

    if isinstance(value, datetime):
        return value.strftime(TIME_FMT)
    elif isinstance(value, date):
        return value.strftime(DATE_FMT)
    elif isinstance(value, Decimal):
        return str(value)
    elif isinstance(value, list):
        tmp_list = []
        tmp_limits = level_limits.copy()
        length = len(value)
        for idx, item in enumerate(value):
            result = _eval_value(
                item, class_name, to_camel_case, tmp_limits)
            tmp_list.append(result)

            if idx < length - 1:
                tmp_limits = level_limits.copy()
            else:
                level_limits = tmp_limits
        return tmp_list

    elif isinstance(value, model.Model):
        res = STOP_VALUE
        if value._class() != class_name:
            res = value.to_dict(to_camel_case, level_limits=level_limits)
        return res

    else:
        return value

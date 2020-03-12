#   dbbase/model.py
"""
This module implements a base model to be used for table creation.

"""
import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.declarative import (
    as_declarative, declared_attr)
from sqlalchemy.util import clsname_as_plain_name

from . db_utils import xlate
from . serializers import _eval_value, STOP_VALUE

@as_declarative()
class Model(object):
    """
    This class attempts to replicate some of the features available when
    using flask_sqlalchemy.

    selected elements are:
        db.session
        db.Model
        cls.query
            used as:
                MyTable.query().filter(MyTable.id == 331)
            in place of:
                session.query(MyTable).filter(MyTable.id == 331)

    To replicate the process, it needs to pull in db as an import to
    each model module
    """
    # catchall for sqlalchemy classes and functions
    db = None

    @property
    @classmethod
    def query(cls):
        """Return query object with class"""
        return cls.db.session.query(cls)

    @declared_attr
    @classmethod
    def __tablename__(cls):
        return cls.__name__.lower()

    def _class(self):
        """
        Returns the class name. For example:

            user.__class__
            is __main__.User

        This function returns User
        """
        return clsname_as_plain_name(self.__class__)
        # return str(self.__class__).split('.')[1]

    def to_dict(self, to_camel_case=True, level_limits=None):
        """
        Returns columns in a dict. The point of this is to make a useful
        default. However, this can't be expected to cover every possibility,
        so of course it can be overwritten in any particular model.

        Conversion defaults:
            date -> %F
            datetime -> %Y-%m-%d %H:%M:%S
            Decimal => str



        """
        self.db.session.flush()
        SA_INDICATOR = '_sa_instance_state'
        class_name = self._class()
        if level_limits is None:
            level_limits = set()

        result = {}
        for key, value in self.__dict__.items():
            if key != SA_INDICATOR:
                if to_camel_case:
                    key = xlate(key, camel_case=True)
                res = _eval_value(
                    value, self._class(), to_camel_case, level_limits)
                if res != STOP_VALUE:
                    result[key] = res
        return result

    def serialize(self, to_camel_case=True, level_limits=None):
        """serialize

        Output JSON formatted model.

        Usage: serialize(self, to_camel_case=True, level_limits=None)

        See help for to_dict for information on to_camel_case

        level_limits:
            an example is most helpful.
            Suppose you have two tables: user and addresses

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
                "Address", back_populates="user")

            the relationship provides a look at the user in the address
            the relationship provides a look at the addresses in user

            If you want to serialize a user and include the addresses
            it might look like:
                user
                    id
                    name
                    addresses
                        address1
                            id
                            user_id
                            email_address

            But here we have a problem. The Address class has the user
            relationship. A recursive process that walks address would then
            include user, which would start the whole loop over again.

            user => address => user => address ... etc


            but if


            user.serialize()


        """
        return json.dumps(
            self.to_dict(to_camel_case=to_camel_case, level_limits=level_limits),
            indent=2    # NOTE: change default?
        )

    @staticmethod
    def deserialize(data, to_camel_case=True):
        """deserialize

        Convert back to column names that are more pythonic.

        Note that this function does not update the model object. That is
        left to another function that can validate the data prior to
        posting.
        """
        if not to_camel_case:
            return data

        result = {}
        for key, value in data:
            key = to_camel_case(key, camel_case=False)
            result[key] = value

        return result

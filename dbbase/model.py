#   dbbase/model.py
"""
This module implements a base model to be used for table creation.

"""
import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.declarative import (
    as_declarative, declared_attr)

from . db_utils import xlate


@as_declarative()
class Model():
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

    def to_dict(self, js_xlate=True):
        """
        Returns columns in a dict. The point of this is to make a useful
        default. However, this can't be expected to cover every possibility,
        so of course it can be overwritten in any particular model.

        Conversion defaults:
            date -> %F
            datetime -> %Y-%m-%d %H:%M:%S
            Decimal => str
        """
        date_fmt = '%F'
        time_fmt = '%Y-%m-%d %H:%M:%S'

        result = {}
        for key, value in self.__dict__.items():
            if key != '_sa_instance_state':
                if js_xlate:
                    key = xlate(key, to_js=True)
                if isinstance(value, datetime):
                    result[key] = value.strftime(time_fmt)
                elif isinstance(value, date):
                    result[key] = value.strftime(date_fmt)
                elif isinstance(value, Decimal):
                    result[key] = str(value)
                else:
                    result[key] = value

        return result

    def serialize(self, js_xlate=True):
        """serialize

        Output JSON formatted model.

        Usage: serialize(self, js_xlate=True)

        See help for to_dict for information on js_xlate

        """
        return json.dumps(self.to_dict(js_xlate=js_xlate))

    @staticmethod
    def deserialize(data, js_xlate=True):
        """deserialize

        Convert back to column names that are more pythonic.

        Note that this function does not update the model object. That is
        left to another function that can validate the data prior to
        posting.
        """
        if not js_xlate:
            return data

        result = {}
        for key, value in data:
            key = js_xlate(key, to_js=False)
            result[key] = value

        return result

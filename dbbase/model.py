#   dbbase/model.py
"""
This module implements a base model to be used for table creation.

"""
import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.util import clsname_as_plain_name
from sqlalchemy.orm import scoped_session

from .utils import xlate
from .serializers import _eval_value, STOP_VALUE, SERIAL_STOPLIST


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

    # constants
    _DEFAULT_SERIAL_STOPLIST = SERIAL_STOPLIST
    SERIAL_STOPLIST = None
    SERIAL_LIST = None

    query = None
    #@classmethod
    #def _query(cls):
        #return  db.orm.Query(cls).with_session(cls.db.session)

    @classmethod
    def _class(cls):
        """
        Returns the class name.

        For example:

            user.__class__
            is __main__.User

            then this function returns 'user'
        """
        return cls.__table__.name.lower()

    @classmethod
    def _get_serial_stop_list(cls):
        """Return default stop list, class stop list."""
        if cls.SERIAL_STOPLIST is None:
            serial_stoplist = []
        else:
            serial_stoplist = cls.SERIAL_STOPLIST
        if not isinstance(serial_stoplist, list):
            raise ValueError(
                "SERIAL_STOPLIST must be a list of one or more fields that"
                "would not be included in a serialization."
            )
        return (
            cls._DEFAULT_SERIAL_STOPLIST +
            SERIAL_STOPLIST +
            serial_stoplist
        )

    def _get_relationship(self, field):
        """_get_relationship

        Usage:
            self,_get_relationship(field)
        Used for iterating through relationships to determine how deep to go
        with serialization.

        returns:
            if a relationship is found, returns the relationship
            otherwise None
        """
        tmp = self.db.inspect(self.__class__).relationships

        if field in tmp.keys():
            return tmp[field]

        return None

    def _relations_info(self, field):
        """
        This function provides info to help determine how far down the path to go
        on serialization of a relationship field.

        Is it self-referential
        One to many
        join_depth
        """
        relation = self._get_relationship(field)
        if relation is not None:
            return {
                'self-referential': relation.target.name == self.__tablename__,
                # these are not currently used.
                # intuitively, it seems like a good idea, but I am not sure why.
                # Accordingly, these may be removed without warning, since
                # program structure and testing does not seem to require them.
                'uselist': relation.uselist,
                'join_depth': relation.join_depth
            }
        return None

    def _has_self_ref(self):
        """_has_self_ref

        This function returns True if one or more relationships are self-
        referential.
        """
        for field in self.get_serial_field_list():
            rel_info = self._relations_info(field)
            if rel_info is not None:
                if rel_info['self-referential']:
                    return True

        return False

    def get_serial_field_list(self):
        """get_serial_field_list

        get_serial_field_list(self, serial_field_list=None)

        This function returns a list of table properties that will be used in
        serialization. To accommodate several entirely reasonable scenarios,
        here are the options to select the right option for any particular
        table. Modifications are either by restricting fields or by creating a
        specific list of fields to include, whichever is most convenient.

        Option 1: the default method

        Return self.get_serial_list() will use
            dir(table_object)
                and then remove housekeeping fields and functions
                such as query, serialize, etc, and any items that start
                with _.

        Option 2: add additional fields to exclude
            the approach as used above, but use self.SERIAL_STOPLIST for
            additional fields to exclude.

            For example, do you want to use firstname, lastname or fullname()?
            self.SERIAL_STOPLIST = ['firstname', 'lastname'] would exclude those
            fields, but all the other default fields would be included.

        Option 3: simply define the fields that you want to include by putting
            them into the class SERIAL_LIST. Only those fields will be
            included in serialization.

        Option 4: use a specific list for a particular situation.
            You have a function that needs only certain fields for a specific
            situation, but normally one of the other options are used. In this
            case
        """
        if self.SERIAL_LIST is not None:
            if not isinstance(self.SERIAL_LIST, list):
                raise ValueError(
                    'SERIAL_LIST must be in the form of a list: {}'.format(
                        self.SERIAL_LIST))
            return self.SERIAL_LIST

        fields = [field for field in dir(self) if not field.startswith('_')]

        return list(set(fields) - set(self._get_serial_stop_list()))

    def to_dict(self, to_camel_case=True, level_limits=None, sort=False):
        """
        Returns columns in a dict. The point of this is to make a useful
        default. However, this can't be expected to cover every possibility,
        so of course it can be overwritten in any particular model.

        Conversion defaults:
            date -> %F
            datetime -> %Y-%m-%d %H:%M:%S
            Decimal => str

        paramaters:
            to_camel_case (boolean)

        }

        """
        self.db.session.flush()
        if level_limits is None:
            level_limits = set()

        if self._class() in level_limits:
            # it has already been done
            if not self._has_self_ref():
                return STOP_VALUE
        result = {}
        field_list = self.get_serial_field_list()
        if sort:
            field_list = sorted(self.get_serial_field_list())

        for key in field_list:
            # special treatment for relationships
            rel_info = self._relations_info(key)
            if rel_info is not None:
                if not rel_info['self-referential'] and self._class() in level_limits:
                    # stop it right there
                    res = STOP_VALUE
                    break
            value = self.__getattribute__(key)

            if callable(value):
                value = value()

            res = _eval_value(
                value, to_camel_case, level_limits, source_class=self._class()
            )

            if to_camel_case:
                key = xlate(key, camel_case=True)

            if res != STOP_VALUE:
                result[key] = res

        if self._class() not in level_limits:
            level_limits.add(self._class())

        return result

    def serialize(
            self, to_camel_case=True, level_limits=None, sort=False,
            indent=None):
        """serialize

        Output JSON formatted model.

        Usage:
            serialize(to_camel_case=True, level_limits=None)

        parameters:
            to_camel_case (boolean) True converts to camel case.
            level_limits (set()) set of lower case class models
                to exclude
            sort (boolean) True will sort the keys alphabetically
            indent (integer) The number of spaces to indent

        return
            JSON formatted string of the data.
        """
        return json.dumps(
            self.to_dict(
                to_camel_case=to_camel_case,
                level_limits=level_limits,
                sort=sort
            ),
            indent=indent
        )

    @staticmethod
    def deserialize(data, from_camel_case=True):
        """deserialize

        Convert back to column names that are more pythonic.

        Note that this function does not update the model object. That is
        left to another function that can validate the data prior to
        posting.
        """
        if isinstance(data, str):
            # assume json
            data = json.loads(data)

        if not from_camel_case:
            return data

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key = xlate(key, camel_case=False)
                result[key] = value

        else:
            # it must be a list
            result = []
            for line in data:
                res = {}
                for key, value in line.items():
                    key = xlate(key, camel_case=False)
                    res[key] = value
                result.append(res)

        return result

    def save(self):
        """save

        This function saves adds and commits the object via session.

        Since this can of course be overwritten in your class to
        provide validation checks prior to saving.

        """
        self.db.session.add(self)
        self.db.session.commit()
        return self

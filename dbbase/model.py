# dbbase/model.py
"""
This module implements a base model to be used for table creation.

"""
import json
from sqlalchemy.ext.declarative import as_declarative

from .utils import xlate
from .serializers import _eval_value, STOP_VALUE, SERIAL_STOPLIST


@as_declarative()
class Model(object):
    """
    This class replicates some of the design features available
    when using flask_sqlalchemy. The primary interest is the embedding of
    references to the database via session and the query object.

    selected elements are:
    * db.session
    * db.Model
    * cls.query

    To replicate the process, it needs to pull in db as an import to
    each model module.

    Serialization:

    There are class variables that can be set for models to control
    what shows for serialization. For more information look at the
    User Guide, but the following are the class variables used for
    this purpose.

    When the following are set at default, `serialize()` will return
    the database columns plus any methods that have been created. To
    automatically exclude a method, name it with a starting _.

    `SERIAL_STOPLIST = None`
    `SERIAL_LIST = None`

    If SERIAL_STOPLIST is a list of column names, those names will be
    excluded from serialization.

    If SERIAL_LIST is a list, serialization will return ONLY those
    names in the list and in that order.
    """
    # catchall for sqlalchemy classes and functions
    db = None

    # constants
    _DEFAULT_SERIAL_STOPLIST = SERIAL_STOPLIST
    SERIAL_STOPLIST = None
    SERIAL_LIST = None

    query = None

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
        return cls._DEFAULT_SERIAL_STOPLIST + SERIAL_STOPLIST + serial_stoplist

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
        This function provides info to help determine how far down
        the path to go on serialization of a relationship field.

        Is it self-referential
        One to many
        join_depth
        """
        relation = self._get_relationship(field)
        if relation is None:
            return None

        return {
            "self-referential": relation.target.name == self.__tablename__,
            # these are not currently used.
            # intuitively, it seems like a good idea, but I am not sure why.
            # Accordingly, these may be removed without warning, since
            # program structure and testing does not seem to require them.
            "uselist": relation.uselist,
            "join_depth": relation.join_depth,
        }

    def _has_self_ref(self):
        """_has_self_ref

        This function returns True if one or more relationships are self-
        referential.
        """
        for field in self.get_serial_field_list():
            rel_info = self._relations_info(field)
            if rel_info is not None:
                if rel_info["self-referential"]:
                    return True

        return False

    def get_serial_field_list(self):
        """get_serial_field_list

        This function returns a list of table properties that will be used in
        serialization. To accommodate several entirely reasonable scenarios,
        here are the options to select the right option for any particular
        table. Modifications are either by restricting fields or by creating a
        specific list of fields to include, whichever is most convenient.

        Default:
            get_serial_field_list()

        Returns:
            serial_fields (list) : current list of fields
        """
        if self.SERIAL_LIST is not None:
            if not isinstance(self.SERIAL_LIST, list):
                raise ValueError(
                    "SERIAL_LIST must be in the form of a list: {}".format(
                        self.SERIAL_LIST
                    )
                )
            return self.SERIAL_LIST

        fields = [field for field in dir(self) if not field.startswith("_")]

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

        Default:
            to_dict(to_camel_case=True, level_limits=None, sort=False)

        paramaters:
            to_camel_case (boolean) : dict keys will be converted to camel
                case.
            level_limits: (set : None) : This is more of a technical parameter
                that is used to limit recursion, but if a class name is
                listed in the set, `to_dict` will not process that class.
            sort: (bool) : This flag determines whether the keys will be
                sorted.
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
                if (
                    not rel_info["self-referential"]
                    and self._class() in level_limits
                ):
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
        self, to_camel_case=True, level_limits=None, sort=False, indent=None
    ):
        """serialize

        Output JSON formatted model.

        Default:
            serialize(to_camel_case=True, level_limits=None, sort=False, indent=None)

        Args:
            to_camel_case (boolean) True converts to camel case.
            level_limits: (set : None) : This is more of a technical parameter
                that is used to limit recursion, but if a class name is
                listed in the set, `to_dict` will not process that class.
            sort: (bool) : This flag determines whether the keys will be
                sorted.
            indent: (integer : None) The number of spaces to indent to improve
                readability.

        return
            JSON formatted string of the data.
        """
        return json.dumps(
            self.to_dict(
                to_camel_case=to_camel_case,
                level_limits=level_limits,
                sort=sort,
            ),
            indent=indent,
        )

    @staticmethod
    def deserialize(data, from_camel_case=True):
        """deserialize

        Convert back to column names that are more pythonic.

        Note that this function does not update the model object. That is
        left to another function that can validate the data prior to
        posting.

        Default:
            deserialize(data, from_camel_case=True)

        Args:
            data: (str : dict) : JSON string that is to be converted back to
                a dict. `data` can also be a dict or list that simply needs to
                have the keys converted to snake_case.
            from_camel_case: (bool) : True will cause the keys to be converted
                back to snake_case.
        Returns:
            data (obj) : the converted data
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

        Default:
            save()

        Return
            saved_obj (obj) : the object that has been saved with
                hopefully an updated identity.

        """
        self.db.session.add(self)
        self.db.session.commit()
        return self

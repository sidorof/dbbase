# dbbase/model.py
"""
This module implements a base model to be used for table creation.

"""
import json
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm.attributes import InstrumentedAttribute

from .utils import xlate
from .serializers import _eval_value, STOP_VALUE, SERIAL_STOPLIST


@as_declarative()
class Model(object):
    """
    This class replicates some of the design features available
    when using flask_sqlalchemy. The primary interest is the embedding of
    references to the database via session and the query object.

    selected elements are

    * `db.session`
    * `db.Model`
    * `cls.query`

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

    * `SERIAL_STOPLIST = None`

    * `SERIAL_FIELDS = None`

    * `SERIAL_FIELD_RELATIONS = None`

    If SERIAL_STOPLIST is a list of column names, those names will be
    excluded from serialization.

    If SERIAL_FIELDS is a list, serialization will return ONLY those
    names in the list and in that order.

    If SERIAL_FIELD_RELATIONS is a dict of related fields and a list
    of fields that would be used as `SERIAL_FIELDS` when serializing
    this class.

    """

    # catchall for sqlalchemy classes and functions
    db = None

    # constants
    _DEFAULT_SERIAL_STOPLIST = SERIAL_STOPLIST
    SERIAL_STOPLIST = None
    SERIAL_FIELDS = None
    SERIAL_FIELD_RELATIONS = None

    query = None

    @classmethod
    def _class(cls):
        """
        Returns the class name.

        For example:

            user.__class__
            is __main__.User

            then this function returns 'User'
        """
        return cls.__name__

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

    @classmethod
    def _get_relationship(cls, field):
        """_get_relationship

        Usage:
            _get_relationship(field)
        Used for iterating through relationships to determine how deep to go
        with serialization.

        returns:
            if a relationship is found, returns the relationship
            otherwise None
        """
        tmp = inspect(cls).relationships

        if field in tmp.keys():
            return tmp[field]

        return None

    @classmethod
    def _relations_info(cls, field):
        """
        This function provides info to help determine how far down
        the path to go on serialization of a relationship field.

        Is it self-referential
        One to many
        join_depth
        """
        relation = cls._get_relationship(field)
        if relation is None:
            return None

        if (relation.back_populates or relation.backref) and relation.uselist:
            bidirectional = True
        else:
            bidirectional = False

        return {
            "self-referential": relation.target.name == cls.__tablename__,
            "uselist": relation.uselist,
            "join_depth": relation.join_depth,
            "lazy": relation.lazy,
            "bidirectional": bidirectional,
        }

    @classmethod
    def _is_bidirectional(self, field):
        """ True if can update relation."""

        rel_info = self._relations_info(field)
        if rel_info:
            return rel_info["bidirectional"]

        return False

    @classmethod
    def _has_self_ref(cls):
        """_has_self_ref

        This function returns True if one or more relationships are self-
        referential.
        """
        for field in cls.get_serial_fields():
            rel_info = cls._relations_info(field)
            if rel_info is not None:
                if rel_info["self-referential"]:
                    return True

        return False

    @classmethod
    def get_serial_fields(cls):
        """get_serial_fields

        This function returns a list of table properties that will be used in
        serialization. To accommodate several entirely reasonable scenarios,
        here are the options to select the right option for any particular
        table. Modifications are either by restricting fields or by creating a
        specific list of fields to include, whichever is most convenient.

        Default:
            get_serial_fields()

        Returns:
            serial_fields (list) : current list of fields
        """
        if cls.SERIAL_FIELDS is not None:
            if not isinstance(cls.SERIAL_FIELDS, list):
                raise ValueError(
                    "SERIAL_FIELDS must be in the form of a list: {}".format(
                        cls.SERIAL_FIELDS
                    )
                )
            return cls.SERIAL_FIELDS

        fields = [field for field in dir(cls) if not field.startswith("_")]

        return list(set(fields) - set(cls._get_serial_stop_list()))

    def to_dict(
        self,
        to_camel_case=True,
        level_limits=None,
        sort=False,
        serial_fields=None,
        serial_field_relations=None,
    ):
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

        Args:
            to_camel_case (boolean) : dict keys will be converted to camel
                case.
            level_limits: (dict : None) : This is more of a technical parameter
                that is used to limit recursion, but if a class name is
                listed in the dict, `to_dict` will not process that class.
            sort: (bool) : This flag determines whether the keys will be
                sorted.
            serial_fields (list) : a list of fields to be substituted for
                `cls.SERIAL_FIELDS`
            serial_field_relations (dict) : To enable a more nuanced control of
                relations objects, the name of a downstream class and a
                list of fields to be typically included with the related
                object.

        Returns:
            (dict) | a dictionary of fields and values
        """
        if level_limits is None:
            level_limits = {}

        if serial_field_relations is None:
            serial_field_relations = {}
            if self.SERIAL_FIELD_RELATIONS is not None:
                serial_field_relations = self.SERIAL_FIELD_RELATIONS

        if self._class() in level_limits:
            # it has already been done
            if not self._has_self_ref():
                return STOP_VALUE

        result = {}

        if serial_fields is None:
            serial_fields = self.get_serial_fields()

        if sort:
            serial_fields = sorted(serial_fields)

        for key in serial_fields:
            # special treatment for relationships
            rel_info = self._relations_info(key)
            if rel_info is not None:
                if (
                    not rel_info["self-referential"]
                    and self._class() in level_limits
                ):
                    # stop it right there
                    res = STOP_VALUE

            value = self.__getattribute__(key)

            if rel_info and rel_info["lazy"] == "dynamic":
                value = [item for item in value.all()]

            status = True

            if self._is_write_only(key):
                if value is not None:
                    status = False

            if status:
                if callable(value):
                    value = value()

                res = _eval_value(
                    value,
                    to_camel_case,
                    level_limits,
                    source_class=self._class(),
                    serial_field_relations=serial_field_relations,
                )

                if to_camel_case:
                    key = xlate(key, camel_case=True)

                if res != STOP_VALUE:
                    result[key] = res

        if self._class() not in level_limits:
            level_limits[self._class()] = 1

        return result

    def serialize(
        self,
        to_camel_case=True,
        level_limits=None,
        sort=False,
        indent=None,
        serial_fields=None,
        serial_field_relations=None,
    ):
        """serialize

        Output JSON formatted model.

        Default:
            serialize(
                to_camel_case=True, level_limits=None, sort=False,
                indent=None, serial_fields=None, serial_field_relations=None
            )

        Args:
            to_camel_case (boolean) True converts to camel case.
            level_limits: (dict : None) : This is more of a technical parameter
                that is used to limit recursion, but if a class name is
                listed in the dict, `to_dict` will not process that class.
            sort: (bool) : This flag determines whether the keys will be
                sorted.
            indent: (integer : None) The number of spaces to indent to improve
                readability.
            serial_fields (None | list) : a list of fields to be substituted
                for `cls.SERIAL_FIELDS`
            serial_field_relations (None | dict) : To enable a more nuanced
                control of relations objects, the name of a downstream class
                and a list of fields to be typically included with the related
                object.

        return
            JSON formatted string of the data.
        """
        return json.dumps(
            self.to_dict(
                to_camel_case=to_camel_case,
                level_limits=level_limits,
                sort=sort,
                serial_fields=serial_fields,
                serial_field_relations=serial_field_relations,
            ),
            indent=indent,
        )

    @classmethod
    def deserialize(cls, data, from_camel_case=True, only_columns=False):
        """deserialize

        Convert back to column names that are more pythonic.

        Note that this function does not update the model object. That is
        left to another function that can validate the data prior to
        posting.

        Default:
            deserialize(data, from_camel_case=True, only_columns=False)

        Args:
            data: (bytes : str : dict) : JSON string that is to be converted
                back to a dict. `data` can also be a dict or list that simply
                needs to have the keys converted to snake_case.
            from_camel_case: (bool) : True will cause the keys to be converted
                back to snake_case.
            only_columns: (bool) : True will cause the keys that are not columns
                to be stripped out.
        Returns:
            data (obj) : the converted data
        """

        def only_column_check(key):
            if key in cls.__dict__:
                if hasattr(cls.__dict__[key], "expression"):
                    return isinstance(
                        cls.__dict__[key].expression, cls.db.Column
                    )
            return False

        if isinstance(data, str) or isinstance(data, bytes):
            # assume json
            data = json.loads(data)

        if not from_camel_case:
            return data

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key = xlate(key, camel_case=False)
                if only_columns:
                    if only_column_check(key):
                        result[key] = value
                else:
                    result[key] = value

        else:
            # it must be a list
            result = []
            for line in data:
                res = {}
                for key, value in line.items():
                    key = xlate(key, camel_case=False)
                    if only_columns:
                        if only_column_check(key):
                            res[key] = value
                    else:
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

    def delete(self):
        """delete

        This function deletes and commits the object via session.

        Since this can of course be overwritten in your class to
        simply mark the record as inactive to avoid losing an
        audit trail.

        Default:
            delete()

        Return
            None
        """
        self.db.session.delete(self)
        self.db.session.commit()

    def _null_columns(self):
        """_null_columns

        This function walks the columns and lists any columns that are null.
        """
        return [
            column.name
            for column in self.__table__.columns
            if getattr(self, column.name) is None
        ]

    def validate_record(self, camel_case=False):
        """validate_record

        This function attempts to report any missing data from a
        record. Intended to be run just prior to saving, the idea is that
        meaningful feedback could be provided without raising an error in
        the database.

        The function walks the record for required fields. If there
        are no defaults, local or server, that will be filled in for that
        column that triggers a report.

        One response is a dict with a key of "missing_values".
        Another response is a dict foreign keys that have no corresponding
        id found in the foreign table.

        Default:
            validate_record(camel_case=False)

        Args:
            camel_case (bool) : error message converted to camel case

        Return
            status (bool) : True if no errors found
            error_dict (None : dict ) | a dict that contains an error list
        """
        errors = []
        tmp = inspect(self.__class__).all_orm_descriptors
        null_cols = self._null_columns()
        for column in null_cols:
            expr = tmp[column].expression
            status = True
            if expr.nullable is False:
                if expr.default is not None:
                    status = False
                if expr.server_default is not None:
                    status = False
                if expr.server_onupdate is not None:
                    status = False
                if expr.primary_key:
                    status = False
                if status:
                    errors.append(column)

        if errors:
            key = "missing_values"
            if camel_case:
                msg = {xlate(key): [xlate(error) for error in errors]}
            else:
                msg = {key: errors}
            return False, msg

        status, errors = self._validate_foreignkeys()
        if errors:
            new_errors = []
            if camel_case:
                for key, error in errors.items():
                    new_errors.append(dict([xlate(key), error]))
                errors = new_errors
            return False, {"ForeignKeys": errors}

        return True, None

    def _validate_foreignkeys(self):
        """_validate_foreignkeys

        This function returns an error message if there is an issue with
        foreign keys.

        If foreign key field cannot be null and no default
        If foreign key is not found in related table
        """
        errors = []
        for key, value in self._extract_foreign_keys().items():
            column_params = self.db.doc_column(self.__class__, key)
            key_value = getattr(self, key)
            if key_value is not None:
                if column_params["nullable"] is False:
                    # foreign key
                    table, id_ = value["foreign_key"].split(".")
                    select = f"select {id_} from {table} where {id_} = {id_}"
                    res = self.db.session.execute(select).first()
                    if res is None:
                        errors.append(
                            {key: f"{key_value} is not a valid foreign key"}
                        )
        if errors:
            return False, errors
        else:
            return True, None

    @classmethod
    def filter_columns(
        cls, column_props, only_props=False, to_camel_case=False
    ):
        """ filter_columns

        This function accepts a model class, a list of column properties to
        of interest. Depending upon the needs, all of the properties for the
        column can be returned once the desired column property is detected,
        it can return columns with only those properties.

        Usage:
            filter_columns(
                column_props,
                only_props=False,
                to_camel_case=False
            )

        Args:
            column_props: (list) : A list of column properties to search for.
                Also, the negative can be found, such as `!readOnly`
            only_props: (bool) : If True, each selected column will contain
                only those column_props selected. If False, column_props act
                as detection system and will return the entire column.
            to_camel_case: (bool) : converts the column names to camel case

        """
        doc = cls.db.doc_table(cls, to_camel_case=to_camel_case)[cls._class()][
            "properties"
        ]

        new_doc = {}
        for column, col_properties in doc.items():
            new_properties = {}
            keys = list(col_properties.keys())
            for prop in column_props:
                if prop.startswith("!"):
                    prop = prop[1:]
                    if prop in keys:
                        if col_properties[prop] is False:
                            if only_props:
                                new_properties[prop] = col_properties[prop]
                            else:
                                new_properties = col_properties
                                break
                    else:
                        new_properties = col_properties
                else:
                    if prop in keys:
                        if col_properties[prop] is not False:
                            if only_props:
                                new_properties[prop] = col_properties[prop]
                            else:
                                new_properties = col_properties
                                break
            if new_properties:
                new_doc[column] = new_properties

        return new_doc

    @classmethod
    def _extract_foreign_keys(cls):
        """ _extract_foreign_keys

        This function walks the document dictionary and returns the
        foreign keys.

        ex. return [('author_id', {'foreign_key': 'authors.id'})]
        """
        return dict(
            [
                (key, value)
                for key, value in cls.filter_columns(
                    column_props=["foreign_key"], only_props=True
                ).items()
                if value
            ]
        )

    @classmethod
    def _is_write_only(cls, column_name):
        """ _is_write_only

        This function returns True if the column has 'writeOnly' True
        in the info field.
        """
        if column_name in cls.__dict__:
            tmp = cls.__dict__[column_name]
            if isinstance(tmp, InstrumentedAttribute):
                if isinstance(tmp.expression, cls.db.Column):
                    if "writeOnly" in tmp.expression.info:
                        value = tmp.expression.info["writeOnly"]
                        return value
        return False

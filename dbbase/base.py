# dbbase/base.py
"""
This module maintains database info common to all the modules.

This implements database creation and dropping. In addition, a
database class takes in a config for the URI of the database.

Because this module implements database creation and dropping,
the config variables must not only have a URI as a string. There
must be also knowledge of a superuser with the rights to perform the
needed actions, and a base database such as with PostgreSQL.

To that end there is also a config function for flexibility.

"""
import logging
import importlib

import sqlalchemy
from sqlalchemy import create_engine, orm, Table
from sqlalchemy.sql.elements import BinaryExpression

from . import model
from .column_types import WriteOnlyColumn
from .serializers import STOP_VALUE
from .utils import xlate
from .doc_utils import (
    process_expression,
    _property,
    _function,
    _binary_expression,
    _foreign_keys,
)


logger = logging.getLogger(__name__)


class DB(object):
    """
    This class defines a central location for accepting database
    configuration information, creating connections and sessions.

    Default:
        DB(config, model_class=None, checkfirst=True, echo=False)

    Args:
        config: (str) : Configuration string for the database,
            the equivalent of SQLALCHEMY_DATABASE_URI.
        model_class: (obj) : An alternate Model class can be inserted.
            Otherwise it defaults to Model in this package.
        checkfirst: (bool) : create tables only if the table
            does not exist
        echo: (bool) : log actions in database engine
    """

    def __init__(
        self,
        config,
        model_class=None,
        checkfirst=True,
        echo=False,
        *args,
        **kwargs
    ):

        # not a fan of this
        if config != ":memory:":
            self.config = config
        else:
            self.config = "sqlite://"

        for key in sqlalchemy.__all__:
            self.__setattr__(key, sqlalchemy.__dict__.__getitem__(key))

        # column types
        self.__setattr__("WriteOnlyColumn", WriteOnlyColumn)

        # these are being added on an as-needed basis
        orm_functions = ["relationship", "aliased", "lazyload"]
        for key in orm_functions:
            self.__setattr__(key, orm.__dict__.__getitem__(key))

        # all of the orm is available here
        self.orm = orm

        self.Model = self.load_model_class(model_class)
        self.Model.db = self

        # now create_session is done after importing models
        self.session = self.create_session(
            checkfirst=checkfirst, echo=echo, *args, **kwargs
        )

    @staticmethod
    def load_model_class(model_class=None):
        """ load_model_class

        This function creates a fresh copy of the declarative base.
        This causes a reset of the metaclass.

        Default:
            load_model_class(model_class=None)

        Args:
            model_class: (obj) : An alternate Model class can be
                inserted. Otherwise it defaults to Model in this
                package.

        Returns:
            model_class (obj)
        """
        importlib.reload(model)
        if model_class is None:
            return model.Model

    def create_engine(self, echo=False, *args, **kwargs):
        """ create_engine

        Basically a pass through to sqlalchemy.

        Default:
            create_engine(echo=False)

        Args:
            config: (str) : Configuration string for the database
            echo: (bool) : log actions in database engine

        Returns:
            engine (obj) : newly created engine
        """
        self.engine = create_engine(self.config, echo=echo)
        return self.engine

    def create_session(self, checkfirst=True, echo=False, *args, **kwargs):
        """create_session

        This function instantiates an engine, and connects to the database.
        A session is initiated. Finally, any new tables are created.

        Default:
            create_session(checkfirst=True, echo=False)

        Args:
            checkfirst: (bool) : If True, will not recreate a table
                that already exists.
            echo: (bool : str) : logs interactions with engine
                to INFO. defaults to False. echo can also be "debug" for more
                detail.

        Returns:
            session (obj)
        """
        engine = create_engine(self.config, echo=echo, *args, **kwargs)
        engine.connect()

        session = orm.sessionmaker(bind=engine)()

        self.Model().metadata.create_all(engine, checkfirst=checkfirst)
        self._apply_db()

        return session

    def drop_all(self, echo=False):
        """ drop_all
        Drop all tables and sequences.

        Leaves the database empty, bereft, alone, a pale shadow of its
        former self.

        Default:
            drop_all(echo=False)

        Args:
            echo: (bool : str) : logs interactions with engine
                to INFO. defaults to False. echo can also be "debug" for more
                detail.
        """
        # see how this session is not the 'session' object
        self.orm.session.close_all_sessions()
        engine = create_engine(self.config, echo=echo)
        self.Model().metadata.drop_all(engine)

    def create_all(self, bind=None, checkfirst=True):
        """create_all

        This function creates all available tables.

        Default:
            create_all(bind=None, checkfirst=True)

        Args:
            bind: (obj) : sqlalchemy.engine.base.Engine
            checkfirst: (bool) : If True, will not recreate a table
                that already exists.
        """
        if bind is None:
            bind = self.session.bind
        self.Model.metadata.create_all(bind, checkfirst=checkfirst)
        self._apply_db()

    def _apply_db(self):
        """ _apply_db

        This function walks the Model classes and inserts the query
        and db objects. Applying db helps in situations where the
        db has changed from the original creation of the Model.
        """
        for cls in self.Model._decl_class_registry.values():
            if hasattr(cls, "__table__"):
                if isinstance(cls.__table__, Table):
                    self.apply_db(cls)

    def apply_db(self, cls):
        """ apply_db
        This function receives a Model class and applies db and session
        to the class. This enables model classes to be added if not in
        the original initialization.

        Args:
            cls: (Model) : the Model class having the attributes updated.
        """
        cls.query = self.session.query(cls)
        cls.db = self

    def doc_tables(self, class_list=None, to_camel_case=False):
        """ doc_tables

        This function creates a dictionary of all the table configuratons.

        The function can be used in several ways:

        * Communicate characteristics about a resource in an API.
        * Provide a basis for unittesting a table to verify settings.
        * Enable API resource validation prior to record creation.

        Usage:
            doc_tables(
                class_list=None
                to_camel_case=False
            )

        Args:
            #class_list: (None : list) : if left as None, returns all classes
            to_camel_case: (bool) : converts the column names to camel case
            serial_fields: (None : list) : specify a limited list of columns

        Return:

            doc (dict) : a dict of the classes with an initial key of
                         'definitions'

        The column props included are name, type, required, default detail,
        foreign_keys, and unique.
        """
        if class_list is None:
            classes = self.Model._decl_class_registry.values()
            class_names = self.Model._decl_class_registry.keys()
        else:
            class_names = [cls.__name__ for cls in class_list]

        classes = [
            self.Model._decl_class_registry[class_name]
            for class_name in sorted(class_names)
        ]

        doc_list = [
            self.doc_table(cls, to_camel_case=to_camel_case)
            for cls in classes
            if isinstance(cls, type) and issubclass(cls, self.Model)
        ]
        doc = {"definitions": {}}
        for doc_cls in doc_list:
            doc["definitions"].update(doc_cls)

        return doc

    def doc_table(
        self,
        cls,
        to_camel_case=False,
        serial_fields=None,
        serial_field_relations=None,
        level_limits=None,
        orig_cls=None,
    ):
        """ doc_table

        This function creates a dictionary of a table configuraton to aid in
        documenting.

        The function can be used in several ways:

        * Communicate characteristics about a resource in an API.
        * Provide a basis for unittesting a table to verify settings.
        * Enable API resource validation prior to record creation.

        Usage:
            doc_table(
                cls,
                to_camel_case=False,
                serial_fields=None,
                serial_field_relations=None,
                level_limits=None,
                orig_cls=None
            )

        Args:
            cls: (class) : the table to be documented
            to_camel_case: (bool) : converts the column names to camel case
            serial_fields: (None : list) : specify a limited list of columns
            serial_field_relations: (None: dict) : Can control what serial
            fields are included in relationships
            level_limits: (None : dict) : A technical variable related to
            preventing runaway recursion. Best to leave it alone.
            orig_cls: (None: str) : A technical variable related to recursion,
            leave this variable alone as well.

        Return:

            doc (dict) : a dict of the column values

        """

        def _post_value(key, item_dict):

            if to_camel_case:
                key = xlate(key)
            properties[key] = item_dict

        if level_limits is None:
            level_limits = {}
            orig_cls = cls._class()

        if cls._class() in level_limits:
            # it has already been done
            if not cls._has_self_ref():
                return STOP_VALUE
            elif level_limits[cls._class()] > 1:
                return STOP_VALUE

        properties = {}
        doc = {
            cls.__name__: {
                "type": "object",
                "properties": properties,
                "xml": cls.__name__,
            }
        }

        if serial_fields is not None:
            columns = serial_fields
        else:
            columns = [
                key
                for key in cls.__dict__.keys()
                if key not in cls._get_serial_stop_list()
            ]

        for key in columns:
            value = cls.__dict__[key]

            if hasattr(value, "expression"):
                if isinstance(value.expression, self.Column):
                    # it is a column
                    item_dict = process_expression(value.expression)
                    # done afterwards because keys in expression can change

                elif isinstance(value.expression, BinaryExpression):
                    var_cls = value.prop.entity.class_._class()
                    if orig_cls is not None and var_cls in level_limits:
                        # avoids erroneous exclusion
                        level_limits.pop(var_cls)

                    # relationship or None
                    item_dict = _binary_expression(
                        value,
                        to_camel_case=to_camel_case,
                        serial_field_relations=serial_field_relations,
                        level_limits=level_limits,
                        bidirectional=cls._is_bidirectional(key),
                    )
                else:
                    item_dict = {
                        "readOnly": True,
                        "unknown": str(value.expression),
                    }
                if item_dict is not None:
                    _post_value(key, item_dict)

            elif isinstance(value, property):

                item_dict = _property(cls, key, value)
                _post_value(key, item_dict)

            elif callable(value):

                item_dict = _function(value)
                if item_dict is not None:
                    _post_value(key, item_dict)

            else:
                # skip as unnecessary
                pass

        table_constraints = self._process_table_args(cls)
        if table_constraints is not None:
            doc.update(table_constraints)

        return doc

    def _process_table_args(self, cls):

        table_args = cls.__dict__.get("__table_args__")
        key = "constraints"
        constraints = []

        if table_args:
            # skipping if table_args is a dict
            #   probably param about schemas, so out of scope
            if isinstance(table_args, tuple):
                for item in table_args:
                    if isinstance(item, self.CheckConstraint):
                        ddict = {"check_constraint": item.sqltext.text}
                        constraints.append(ddict)

                    elif isinstance(item, self.ForeignKeyConstraint):
                        fk_key = "foreign_key_constraint"
                        ddict = {fk_key: {}}
                        ddict[fk_key].update(_foreign_keys(item.elements))
                        ddict[fk_key].update({"column_keys": item.column_keys})

                        constraints.append(ddict)

                    elif isinstance(item, self.UniqueConstraint):
                        ddict = {"unique_contraint": {"columns": []}}
                        for uniq_col in item.columns:
                            ddict["unique_contraint"]["columns"].append(
                                uniq_col.expression.name
                            )
                        constraints.append(ddict)
        if constraints:
            return {key: constraints}

        return None

    def doc_column(self, cls, column_name):
        """ doc_column

        This function extracts the documentation dictionary for a column.

        Args:
            cls : (class) : the class that the column belongs to.
            column_name : (str) : the name of the column to be documented.

        Returns:
            dict
        """
        return process_expression(getattr(cls, column_name).expression)

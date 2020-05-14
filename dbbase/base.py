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
from sqlalchemy import create_engine, orm

from . import model
from .utils import xlate
from .doc_utils import process_expression


logger = logging.getLogger(__file__)


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

    def __init__(self, config, model_class=None, checkfirst=True, echo=False):

        # not a fan of this
        if config != ":memory:":
            self.config = config
        else:
            self.config = "sqlite://"

        for key in sqlalchemy.__all__:
            self.__setattr__(key, sqlalchemy.__dict__.__getitem__(key))

        # these are being added on an as-needed basis
        orm_functions = ["relationship", "aliased", "lazyload"]
        for key in orm_functions:
            self.__setattr__(key, orm.__dict__.__getitem__(key))

        # all of the orm is available here
        self.orm = orm

        self.Model = self.load_model_class(model_class)
        self.Model.db = self

        # now create_session is done after importing models
        self.session = self.create_session(checkfirst=checkfirst, echo=echo)

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

    def create_engine(self, echo=False):
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

    def create_session(self, checkfirst=True, echo=False):
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
        engine = create_engine(self.config, echo=echo)
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
            if hasattr(cls, '__table__'):
                if isinstance(cls.__table__, self.Table):
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

    def doc_tables(
            self, class_list=None, to_camel_case=False, column_props=None):
        """ doc_tables

        This function creates a dictionary of all the table configuratons.

        The function can be used in several ways:

        * Communicate characteristics about a resource in an API.
        * Provide a basis for unittesting a table to verify settings.
        * Enable API resource validation prior to record creation.

        Usage:
            doc_tables(
                class_list=None
                to_camel_case=False,
                column_props=None
            )

        Args:
            #class_list: (None : list) : if left as None, returns all classes
            to_camel_case: (bool) : converts the column names to camel case
            serial_list: (None : list) : specify a limited list of columns
            column_props: (None : list) : filter column details to specific
                                          items

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
            for class_name in sorted(class_names)]

        doc_list = [
            self.doc_table(
                cls, to_camel_case=to_camel_case, column_props=column_props)
            for cls in classes
            if isinstance(cls, type) and issubclass(cls, self.Model)
        ]
        doc = {'definitions': {}}
        for doc_cls in doc_list:
            doc['definitions'].update(doc_cls)

        return doc

    def doc_table(
            self, cls, to_camel_case=False, serial_list=None,
            column_props=None):
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
                serial_list=None,
                column_props=None
            )

        Args:
            cls: (class) : the table to be documented
            to_camel_case: (bool) : converts the column names to camel case
            serial_list: (None : list) : specify a limited list of columns
            column_props: (None : list) : filter column details to specific
                                          items

        Return:

            doc (dict) : a dict of the column values

        The column props included are name, type, required, default detail,
        foreign_keys, and unique.
        """

        properties = {}
        doc = {
            cls.__name__: {
                'type': 'object',
                'properties': properties,
                'xml': cls.__name__
            }
        }
        tmp = self.inspect(cls).all_orm_descriptors
        if serial_list is not None:
            columns = serial_list
        else:
            columns = tmp.keys()

        for key in columns:
            value = tmp[key]
            # weed out relations
            if isinstance(value.expression, self.Column):
                item_dict = process_expression(value.expression)
                # done afterwards because keys in expression can change
                if column_props is not None:
                    for prop_key in list(item_dict.keys()):
                        if prop_key not in column_props:
                            del item_dict[prop_key]

                if to_camel_case:
                    key = xlate(key)

                properties[key] = item_dict

        return doc

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
import os
import logging
import importlib

import sqlalchemy
from sqlalchemy import create_engine, orm

from . import model
from .utils import _is_sqlite

logger = logging.getLogger(__file__)


class DB(object):
    """
    This class defines a central location for accepting database configuration information, creating connections and sessions.

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
                to INFO. defaults to False. echo can also be "debug" for more detail.

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
                to INFO. defaults to False. echo can also be "debug" for more detail.
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

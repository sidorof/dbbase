# dbbase/db.py
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
import sys
import os
import logging
import importlib

import sqlalchemy
from sqlalchemy import create_engine, orm
from sqlalchemy.pool import NullPool

from . import model
from .db_utils import is_sqlite

logger = logging.getLogger(__file__)


# if 'SQLALCHEMY_DATABASE_URI' in os.environ:
#     SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
# else:
#     MSG = ''.join([
#         'SQLALCHEMY_DATABASE_URI must be found in the environment.',
#         "The URI will look something like 'sqlite:///{db_file}.db'",
#         "or 'postgresql://{db_username}:{db_password}@{db_host}: ",
#         "{db_port}/{dbname}'",
#         "or mysql+pymysql://{username}:{password}@",
#         "{endpoint}:{port}/{database}?charset=utf8"
#     ])
#     logger.error(
#         'SQLALCHEMY_DATABASE_URI must be found in the environment.')
#     logger.error(MSG)
#     sys.exit(1)


class DB(object):
    """
    Class that holds sqlalchemy items, not intended to be as
    comprehensive as flask_sqlalchemy.

    Usage:
        config, model_class=None, checkfirst=True, echo=False)

        config:
            SQLALCHEMY_DATABASE_URI
        model_class:
            Model class or equivalent
        checkfirst:
            create tables only if the table does not exist
        echo:
            log actions in database engine
    """
    def __init__(
            self, config, model_class=None, checkfirst=True, echo=False):

        # not a fan of this
        if config != ':memory:':
            self.config = config
        else:
            self.config = 'sqlite://'

        for key in sqlalchemy.__all__:
            self.__setattr__(key, sqlalchemy.__dict__.__getitem__(key))

        # just starting with relationship
        orm_functions = ['relationship']
        for key in orm_functions:
            self.__setattr__(key, orm.__dict__.__getitem__(key))

        # all of the orm is put here
        self.orm = orm

        self.Model = self.load_model_class(model_class)

        self.Model = model.Model
        self.Model.db = self
        self.session = self.create_session(checkfirst=checkfirst, echo=echo)

    @staticmethod
    def load_model_class(model_class=None):
        """Creates a fresh copy of the declarative base."""
        importlib.reload(model)
        if model_class is None:
            return model.Model

    def create_engine(self, echo=False):
        """Create engine

        Basically a pass through to sqlalchemy.

        Usage:
            sef.create_engine(echo=False)

        config: SQLALCHEMY_DATABASE_URI
        echo: shows output

        return: engine
        """
        return create_engine(self.config, echo=echo)

    def create_session(self, checkfirst=True, echo=False):
        """create_session

        This function instantiates an engine, and connects to the database.
        A session is initiated. Finally, any new tables are created.

        Usage:
            self.create_session(checkfirst=True, echo=False)

            checkfirst:
                does not create a table if it already exists
                defaults to True
            echo:
                logs interactions with engine to INFO
                defaults to False
                echo can also be "debug" for more detail
        """
        engine = create_engine(self.config, echo=echo)
        engine.connect()

        session = orm.sessionmaker(bind=engine)()

        self.Model().metadata.create_all(engine, checkfirst=checkfirst)

        self.session = session
        return session

    def drop_all(self, echo=False):
        """
        Drop all tables and sequences.

        Leaves the database empty, bereft, alone, a pale shadow of its
        former self.
        """
        # see how this session is not the 'session' object
        self.orm.session.close_all_sessions()
        engine = create_engine(self.config, echo=echo)
        self.Model().metadata.drop_all(engine)


def create_database(config, dbname, superuser=None):
    """
    Creates a new database.

    Usage:

        create_database(
            config,
            dbname,
            superuser=None
        )

    Note that if a superuser is included in the config, that user must have
    permissions to create a database.
    """
    if is_sqlite(config):
        # sqlite does not use CREATE DATABASE
        return
    engine = create_engine(config)

    conn = engine.connect()
    conn.execute("COMMIT;")
    conn.execute(f"CREATE DATABASE {dbname};")

    conn.execute(
        f"GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {superuser};")
    conn.execute(f"ALTER ROLE {superuser} SUPERUSER;")

    conn.close()
    engine.dispose()


def drop_database(config, dbname):
    """Drops a database """

    if is_sqlite(config):
        # sqlite does not use drop database
        if config.find('memory') == -1:
            filename = config[config.find('///') + 3:]
            if os.path.exists(filename):
                os.remove(filename)
    else:
        engine = create_engine(config, poolclass=NullPool)

        conn = engine.connect()
        conn.execute("COMMIT")
        result = conn.execute(f"DROP DATABASE IF EXISTS {dbname}")
        result.close()
        conn.close()
        engine.dispose()

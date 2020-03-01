# dbbase/db.py
"""
This module maintains database info common to all the modules.

"""
import json
import string
from inspect import getmembers
from datetime import date, datetime
from decimal import Decimal

import sqlalchemy
from sqlalchemy.ext.declarative import (
    declarative_base, as_declarative, declared_attr)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Model


class DB(object):
    """
    Class that holds sqlalchemy items, not intended to be as
    comprehensive as flask_sqlalchemy.
    """
    def __init__(self, cls_name=None):
        self.session = None
        for key, value in dict(getmembers(sqlalchemy)).items():
            self.__setattr__(key, value)

        if cls_name is not None:
            self.Model = cls_name
        else:
            self.Model = Model
        self.Model.db = self

    def set_session(self, session):
        self.session = session


db = DB()


DEFAULT_CONFIG = {
  "POSTGRES_CONFIG": "postgresql://localhost:5432/postgres",
  "DB_CONFIG": "postgresql://localhost:5432/%s",
  "SUSER": None
}


def load_settings(filename=None):
    """load_settings

    load_settings(filename=None)

    filename must use JSON format similar to:

        "POSTGRES_CONFIG": "postgresql://localhost:5432/postgres",
        "DB_CONFIG": "postgresql://localhost:5432/%s",
        "SUSER": super_user
        }
    """
    with open(filename) as fobj:
        config = json.load(fobj)

    return config


config = DEFAULT_CONFIG


def create_database(
    dbname, config=config['POSTGRES_CONFIG'], superuser=config['SUSER']):
    """
    Creates a new postgres database.

    Usage:

        create_database(dbname, config=POSTGRES_CONFIG, superuser='don')

    """
    if superuser is None:
        raise ValueError('Invalid superuser')

    engine = create_engine(config)

    conn = engine.connect()

    conn.execute("COMMIT")
    conn.execute("CREATE DATABASE %s" % (dbname))
    conn.execute(
        "GRANT ALL PRIVILEGES ON DATABASE %s TO %s;" % (
            dbname, superuser))
    conn.execute("ALTER ROLE %s SUPERUSER;" % superuser)

    conn.close()


def drop_database(dbname, config=config['POSTGRES_CONFIG']):
    """Drops a new postgres database """

    engine = create_engine(config)

    conn = engine.connect()
    conn.execute("COMMIT")
    result = conn.execute("drop database %s" % (dbname))
    result.close()  # NOTE: both?
    conn.close()


def drop_all(dbname, dbconfig=None, echo=False):
    """
    Drop all tables and sequences.
    """
    if dbconfig is None:
        dbconfig = config['DB_CONFIG'] % (dbname)

    engine = create_engine(dbconfig, echo=echo)
    db.Model().metadata.drop_all(engine)


def init_session(
        dbname, dbconfig=None, echo=False):
    """
    This function sets up a session with the database.

    init_session(
        dbname,             schema name
        dbconfig=None)
        echo=false
    """

    if dbconfig is None:
        dbconfig = config['DB_CONFIG'] % (dbname)

    engine = create_engine(dbconfig, echo=echo)
    conn = engine.connect()

    Session = sessionmaker(bind=engine)
    session = Session()
    db.set_session(session)

    db.Model().metadata.create_all(engine, checkfirst=True)

    return session

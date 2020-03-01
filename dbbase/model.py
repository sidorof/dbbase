#   dbbase/model.py
"""
This module implements a base model to be used for table creation.

"""
import json
import string
from inspect import getmembers
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.declarative import (
    as_declarative, declared_attr)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def query(cls):
        """Return query object with class"""
        return cls.db.session.query(cls)

    def to_dict(self, js_xlate=True):
        """
        Returns columns in a dict. The point of this is to make a useful default

        This can't be expected to cover every possibility.

        Conversion defaults:
            date -> %F
            datetime -> %Y-%m-%d %H:%M:%S
            Decimal => str
        """
        DATE_FMT = '%F'
        TIME_FMT = '%Y-%m-%d %H:%M:%S'

        result = {}
        for key, value in self.__dict__.items():
            if key != '_sa_instance_state':
                if js_xlate:
                    key = xlate(key, to_js=True)
                if isinstance(value, datetime):
                    result[key] = value.strftime(TIME_FMT)
                elif isinstance(value, date):
                    result[key] = value.strftime(DATE_FMT)
                elif isinstance(value, Decimal):
                    result[key] = str(value)
                else:
                    result[key] = value

        return result

    @staticmethod
    def from_JSON(data, js_xlate=True):
        """Convert back to column names that are more pythonic."""
        if not js_xlate:
            return data

        result = {}
        for key, value in data:
            key = js_xlate(key, to_js=False)
            result[key] = value

        return result


def xlate(key, to_js=True):
    """
    This function converts a name to a format used in JavaScript.

    With competing formating standards i
    examples, to_js is True:
        start_date would become startDate
        startdate would remain startdate

    examples, to_js is False:
        startDate would become start_date
        startdate would remain startdate

    """
    if to_js:
        return _js_xlate_to_js(key)
    else:
        return _js_xlate_from_js(key)


def _js_xlate_to_js(key):
    if key.find('_') > -1:
        key = string.capwords(key.replace('_', ' ')).replace(' ', '')
        key = key[0].lower() + key[1:]
    return key


def _js_xlate_from_js(key):
    new_key = ''
    for i in range(len(key)):
        if key[i] in string.ascii_uppercase:
            new_key += '_' + key[i].lower()
        else:
            new_key += key[i]
    return new_key


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


def refresh_matview(session, view):
    """
    This function refreshes a materialized view.
    """
    session.execute('refresh materialized view %s' % (view))
    session.commit()

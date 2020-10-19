# dbbase/utils.py
"""
This module implements some utilities.
"""
import string
import json
import logging

logger = logging.getLogger(__file__)


def db_config(base, config_vars=None):
    """
    This function combines config variables with a base string.

    It is a convenience function for combining data elements
    to make a string that represents a database URI.

    Default:
        db_config(base, config_vars=None)

    Args:
        base: (str) : a string that is the db template, such as
            `"postgresql://{user}:{pass}@{host}:{port}/{dbname}"`
        config_vars: (dict) : variables that will be combined with the base.
        For example:
            'user': 'auser',
            'pass': '123',
            'host': 'localhost',
            'port': 5432,
            'dbname': 'mydatadb'

    config_vars can also be a string that successfully converts from JSON
    to a dict.

    This enables a config to be as simplistic or complex as the situation
    warrants.

    Returns:
        completed_URI (str) : the database URI

    """
    if config_vars is None:
        config_vars = {}
    if isinstance(config_vars, str):
        # try to convert from json
        config_vars = json.loads(config_vars)

    if isinstance(config_vars, dict):
        return base.format(**config_vars)
    return base


def _is_sqlite(config):
    """_is_sqlite

    Default:
        _is_sqlite(config)
    returns True if config contains the string sqlite
    returns True if config contains :memory:
    """
    if config.find("sqlite") > -1:
        return True

    if config.find(":memory:") > -1:
        return True
    return False


def xlate(key, camel_case=True):
    """
    This function translates a name to camel case or back.

    Default:
        xlate(key, camel_case=True)

    Example:
        camel_case is True:
        start_date would become startDate
        startdate would remain startdate

        camel_case is False:
        startDate would become start_date
        startdate would remain startdate

    Args:
        key: (str) : the key that would be converted
        camel_case: (bool) : True to convert to camel case

    Returns:
        key (str) : the converted string

    """
    if camel_case:
        return _xlate_camel_case(key)

    return _xlate_from_camel_case(key)


def _xlate_camel_case(key):
    """Convert example: start_date -> startDate """
    if key.find("_") > -1:
        key = string.capwords(key.replace("_", " ")).replace(" ", "")
        key = key[0].lower() + key[1:]
    return key


def _xlate_from_camel_case(key):
    """Convert example: startDate -> start_date """
    new_key = ""
    for char in key:
        if char in string.ascii_uppercase:
            new_key += "_" + char.lower()
        else:
            new_key += char
    if new_key.startswith("_"):
        new_key = new_key[1:]
    return new_key


def get_model_defaults(cls):
    """
    This function receives a model class and returns the default values
    for the class in the form of a dict.

    If the default value is a function, the function will be executed. This is meant for simple functions such as datetime and uuid.

    Args:
        cls: (obj) : A Model class.

    Returns:
        defaults: (dict) : A dictionary of the default values.
    """
    tmp = {}
    for key in cls.__dict__.keys():
        col = cls.__dict__[key]
        if hasattr(col, "expression"):
            if col.expression.default is not None:
                arg = col.expression.default.arg
                if callable(arg):
                    tmp[key] = arg(cls.db)
                else:
                    tmp[key] = arg
    return tmp

# dbbase/db_utils.py
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

    Usage:
        base: string such as
            postgresql://{user}:{pass}@{host}:{port}/{dbname}"
        config_vars: dict such as
            {
                'user': 'auser',
                'pass': '123',
                'host': 'localhost',
                'port': 5432,
                'dbname': 'mydatadb'
            }

    config_vars can also be a string that successfully converts from JSON
    to a dict.

    This enables a config to be as simplistic or complex as the situation
    warrants.

    Returns a completed URI
    """
    if config_vars is None:
        config_vars = {}
    if isinstance(config_vars, str):
        # try to convert from json
        config_vars = json.loads(config_vars)

    if isinstance(config_vars, dict):
        return base.format(**config_vars)
    return base


def is_sqlite(config):
    """is_sqlite

    returns True if config contains the string sqlite
    returns True if config contains :memory:

    Usage:
        is_sqlite(config)

    """
    if config.find('sqlite') > -1:
        return True

    if config.find(':memory:') > -1:
        return True
    return False


def xlate(key, to_js=True):
    """
    This function translates a name to a format used in JavaScript.

    With competing formating standards i
    examples, to_js is True:
        start_date would become startDate
        startdate would remain startdate

    examples, to_js is False:
        startDate would become start_date
        startdate would remain startdate

    """
    if to_js:
        return _xlate_to_js(key)

    return _xlate_from_js(key)


def _xlate_to_js(key):
    """Convert example: start_date -> startDate """
    if key.find('_') > -1:
        key = string.capwords(key.replace('_', ' ')).replace(' ', '')
        key = key[0].lower() + key[1:]
    return key


def _xlate_from_js(key):
    """Convert example: startDate -> start_date """
    new_key = ''
    for char in key:
        if char in string.ascii_uppercase:
            new_key += '_' + char.lower()
        else:
            new_key += char
    return new_key

"""
This package implements base routines for interacting with the database.
"""
__version__ = '0.1.1'
__author__ = 'Don Smiley'

from . model import Model
from . dbinfo import DB, create_database, drop_database
from . db_utils import db_config, is_sqlite, xlate
from . serializers import _eval_value

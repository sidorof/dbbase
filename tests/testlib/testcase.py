# tests/testlib.testcase.py
"""
To be fully tested with databases other than sqlite, there must be
valid URI for normal connections and a URI for database creation and drop.
In the case of sqlite, it can be one and the same. For a database like
postgresql, the situation is different.

Example 1: sqlite
    URI = 'sqlite:///{test_db}.db'
    TESTDB_URI = 'testdb'

    Can be created, cleared, dropped with one value.

Example 2: postgresql
    TESTDB_URI = 'testdb'

    But to create it, it needs to connect to postgresql server
    in some fashion prior to creating the database. Something along
    the lines of:
    TESTDB_URI = 'testdb'
    BASE_DB = 'postgres'
    SUPERUSER = 'superuser'
    URI = 'postgresql://{superuser}:{password}@{host}:{port}/{basedb}'
    BASE_URI = 'postgresql://{superuser}:{password}@{host}:{port}/{basedb}'

To test then for sqlite, one URI can be used

"""
import os
import sys
import json
import unittest
import subprocess
import sqlalchemy
from sqlalchemy.exc import SAWarning, IntegrityError
import warnings

import dbbase


class BaseTestCase(unittest.TestCase):
    """
    Base class used for testing non-database utility functions.
    """
    dbbase = dbbase


class DBBaseTestCase(BaseTestCase):
    """
    All test cases inherit from this class.

    """
    dbbase = dbbase

    @classmethod
    def setUpClass(cls):
        """
        This doesn't check defaults.'
        """
        dbname = cls.TESTDB_VARS.get('dbname')
        dbbase.dbinfo.drop_database(cls.TESTDB_URI, dbname)
        dbbase.dbinfo.create_database(
            dbname=dbname,
            config=dbbase.db_utils.db_config(
                cls.TESTDB_URI, cls.TESTDB_VARS),
            superuser=cls.TESTDB_VARS.get('suser')
        )

    def setUp(self):
        """Standard configuration."""
        self.db = self.dbbase.DB(
            self.dbbase.db_utils.db_config(
                self.TESTDB_URI, self.TESTDB_VARS
            ) # model_class default as Model
        )

    def verify_requireds(self, obj, req_dict):
        """
        This function receives object and dict of requireds.

        Up to n - 1, an error is raised, then it goes through if all is well.
        """
        rlist = list(req_dict.items())
        length = len(rlist)
        for i in range(length):
            key, value = rlist[i]
            obj.__setattr__(key, value)
            if i < length - 1:
                self.assertRaises(
                    IntegrityError,
                    self.db.session.add(obj))
                self.db.session.rollback()
            else:
                self.db.session.add(obj)
                self.db.session.commit()
                return obj

    def tearDown(self):
        self.db.session.close()

    @classmethod
    def tearDownClass(cls):
        dbname = cls.TESTDB_VARS.get('dbname')
        dbbase.dbinfo.drop_database(cls.TESTDB_URI, dbname)


if __name__ == '__main__':
    unittest.main()

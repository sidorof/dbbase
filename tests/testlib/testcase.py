# tests/testlib.testcase.py
import os
import unittest
import subprocess
import sqlalchemy
from sqlalchemy.exc import SAWarning, IntegrityError
import warnings

#import dbbase

TEMP_DB = 'testdb'

SUPERUSER = (os.environ.get('DBUSER', None) or '').strip()

input('SUPERUSER: %s' % SUPERUSER)

class BaseTestCase(unittest.TestCase):
    """
    All test cases inherit from this class.

    """
    dbbase = dbbase

    def setUpClass():
        """
        This doesn't check defaults.'
        """
        try:
            dbbase.db_common.drop_database(TEMP_DB)
            print("dropped %s database" % (TEMP_DB))
        except Exception as err:
            print('error raised: %s' % (err))

        dbbase.db_common.create_database(TEMP_DB, superuser=SUSER)

    def setUp(self):
        self.dbname = TEMP_DB    # the point?

        self.session = dbbase.init_session(self.dbname)

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
                    self.session.add(obj))
                self.session.rollback()
            else:
                self.session.add(obj)
                self.session.commit()
                return obj

    def tearDown(self):
        self.session.close()

    def tearDownClass():

        dbbase.db_common.drop_database(TEMP_DB)

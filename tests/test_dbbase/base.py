# test/test_dbbase/base.py
from . import DBBaseTestCase

import sqlalchemy


class TestDBBaseClass(DBBaseTestCase):
    """
    This class tests DB class functions

    Deferred this due to the test fixture using all of these
    anyway.
    """

    def test__DB__init__(self):
        """ test__DB__init__

        """
        DB = self.dbbase.DB
        Model = self.dbbase.model.Model

        # test defaults
        # must have config
        self.assertRaises(TypeError, DB)

        db = DB(self.config)
        self.assertIsInstance(db, DB)

        self.assertEqual(db.config, self.config)

        # NOTE: could do testing of essential
        #       attributes of Model

        self.assertEqual(db, db.Model.db)

        # If create_session moved out no need to
        #   check for checkfirst, echo here
        # checkfirst True/False goes here

        # echo

        # test self.attributes

    def test_create_engine(self):
        pass
        # test defaults

        # test self.attributes

        # test return

    def test_create_session(self):
        pass
         # test defaults

        # test self.attributes

        # test return


    def test_drop_all(self):
        pass
         # test defaults

        # test self.attributes

        # test return


    def test_reload_model(self):
        pass
         # test defaults

        # test self.attributes

        # test return


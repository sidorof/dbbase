# test_dbbase/test_utils.py
from . import BaseTestCase
import json

class TestUtilities(BaseTestCase):

    def test_dbconfig(self):
        """Test configurations

        db_config(base, config_vars=None)
        """
        # no config_vars
        base = 'test'
        self.assertEqual(
            base,
            self.dbbase.db_utils.db_config(
                base))

        # with config_vars
        base = 'sqlite:///{db_file}.db'
        config_vars = {'db_file': 'testdb'}
        self.assertEqual(
            'sqlite:///testdb.db',
            self.dbbase.db_utils.db_config(
                base,
                config_vars))

        # with config_vars that are not to included in the uri
        base = 'sqlite:///{db_file}.db'
        config_vars = {'db_file': 'testdb', 'superuser': 'unnecessary'}
        self.assertEqual(
            'sqlite:///testdb.db',
            self.dbbase.db_utils.db_config(
                base,
                config_vars))

        # if config_vars that are in the form of JSON taken directly
        #   from environment variables
        base = 'sqlite:///{db_file}.db'
        config_vars = json.dumps(
            {'db_file': 'testdb', 'superuser': 'unnecessary'})
        self.assertEqual(
            'sqlite:///testdb.db',
            self.dbbase.db_utils.db_config(
                base,
                config_vars))

        # if config_vars that are in the form of JSON taken directly
        #   from environment variables
        base = 'sqlite:///{db_file}.db'
        config_vars = "this is a test"
        self.assertRaises(
            json.decoder.JSONDecodeError,
            self.dbbase.db_utils.db_config,
            base,
            config_vars)


    def test_is_sqlite(self):
        """Test whether the config is for sqlite."""
        config = 'sqlite:///{test_db}.db'
        self.assertTrue(self.dbbase.db_utils.is_sqlite(config))

        config = ':memory:'
        self.assertTrue(self.dbbase.db_utils.is_sqlite(config))

        config = 'postgresql://blah, blah'
        self.assertFalse(self.dbbase.db_utils.is_sqlite(config))

    def test_xlate(self):
        """Test conversion of format for key names."""
        xlate = self.dbbase.db_utils.xlate

        # tests default as well
        key = 'start_date'
        self.assertEqual(xlate(key), 'startDate')

        key = 'start_date'
        self.assertEqual(xlate(key, to_js=True), 'startDate')

        key = 'startDate'
        self.assertEqual(xlate(key, to_js=False), 'start_date')

        key = 'thisIsALotOfCapitals'
        self.assertEqual(
            xlate(key, to_js=False), 'this_is_a_lot_of_capitals')

    def test_xlate_to_js(self):
        """Test conversion for js formatting."""
        _xlate_to_js = self.dbbase.db_utils._xlate_to_js

        key = 'start_date'
        self.assertEqual(_xlate_to_js(key), 'startDate')

    def test_xlate_from_js(self):
        """Test conversion from js formatting to python."""
        _xlate_from_js = self.dbbase.db_utils._xlate_from_js

        key = 'startDate'
        self.assertEqual(_xlate_from_js(key), 'start_date')


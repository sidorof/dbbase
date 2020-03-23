# tests/test_dbbase/utils.py
"""This module tests utility functions."""
import json

from . import BaseTestCase


class TestUtilities(BaseTestCase):
    """Test utilities."""

    def test_dbconfig(self):
        """Test configurations

        db_config(base, config_vars=None)
        """
        # no config_vars
        base = "test"
        self.assertEqual(base, self.dbbase.utils.db_config(base))

        # with config_vars
        base = "sqlite:///{db_file}.db"
        config_vars = {"db_file": "testdb"}
        self.assertEqual(
            "sqlite:///testdb.db",
            self.dbbase.utils.db_config(base, config_vars),
        )

        # with config_vars that are not to included in the uri
        base = "sqlite:///{db_file}.db"
        config_vars = {"db_file": "testdb", "superuser": "unnecessary"}
        self.assertEqual(
            "sqlite:///testdb.db",
            self.dbbase.utils.db_config(base, config_vars),
        )

        # if config_vars that are in the form of JSON taken directly
        #   from environment variables
        base = "sqlite:///{db_file}.db"
        config_vars = json.dumps(
            {"db_file": "testdb", "superuser": "unnecessary"}
        )
        self.assertEqual(
            "sqlite:///testdb.db",
            self.dbbase.utils.db_config(base, config_vars),
        )

        # if config_vars that are in the form of JSON taken directly
        #   from environment variables
        base = "sqlite:///{db_file}.db"
        config_vars = "this is a test"
        self.assertRaises(
            json.decoder.JSONDecodeError,
            self.dbbase.utils.db_config,
            base,
            config_vars,
        )

    def test__is_sqlite(self):
        """Test whether the config is for sqlite."""
        config = "sqlite:///{test_db}.db"
        self.assertTrue(self.dbbase.utils._is_sqlite(config))

        config = ":memory:"
        self.assertTrue(self.dbbase.utils._is_sqlite(config))

        config = "postgresql://blah, blah"
        self.assertFalse(self.dbbase.utils._is_sqlite(config))

    def test_xlate(self):
        """Test conversion of format for key names."""
        xlate = self.dbbase.utils.xlate

        # tests default as well
        key = "start_date"
        self.assertEqual(xlate(key), "startDate")

        key = "start_date"
        self.assertEqual(xlate(key, camel_case=True), "startDate")

        key = "startDate"
        self.assertEqual(xlate(key, camel_case=False), "start_date")

        key = "thisIsALotOfCapitals"
        self.assertEqual(
            xlate(key, camel_case=False), "this_is_a_lot_of_capitals"
        )

    def test_xlate_camel_case(self):
        """Test conversion for js formatting."""
        _xlate_camel_case = self.dbbase.utils._xlate_camel_case

        key = "start_date"
        self.assertEqual(_xlate_camel_case(key), "startDate")

    def test_xlate_from_js(self):
        """Test conversion from js formatting to python."""
        _xlate_from_js = self.dbbase.utils._xlate_from_js

        key = "startDate"
        self.assertEqual(_xlate_from_js(key), "start_date")

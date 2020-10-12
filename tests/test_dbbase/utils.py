# tests/test_dbbase/utils.py
"""This module tests utility functions."""
from datetime import date, datetime
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
        self.assertEqual(self.dbbase.utils.db_config(base), base)

        # with config_vars
        base = "sqlite:///{db_file}.db"
        config_vars = {"db_file": "testdb"}
        self.assertEqual(
            self.dbbase.utils.db_config(base, config_vars),
            "sqlite:///testdb.db",
        )

        # with config_vars that are not to included in the uri
        base = "sqlite:///{db_file}.db"
        config_vars = {"db_file": "testdb", "superuser": "unnecessary"}
        self.assertEqual(
            self.dbbase.utils.db_config(base, config_vars),
            "sqlite:///testdb.db",
        )

        # if config_vars that are in the form of JSON taken directly
        #   from environment variables
        base = "sqlite:///{db_file}.db"
        config_vars = json.dumps(
            {"db_file": "testdb", "superuser": "unnecessary"}
        )
        self.assertEqual(
            self.dbbase.utils.db_config(base, config_vars),
            "sqlite:///testdb.db",
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

    def test_xlate_from_camel_case(self):
        """Test conversion from js formatting to python."""
        _xlate_from_camel_case = self.dbbase.utils._xlate_from_camel_case

        key = "startDate"
        self.assertEqual(_xlate_from_camel_case(key), "start_date")

        # shoehorned in
        key = "StartDate"
        self.assertEqual(_xlate_from_camel_case(key), "start_date")


    def test_get_model_defaults(self):
        """
        This test creates a model with defaults
        and tests whether the defaults are
        identified correctly.
        """
        import uuid
        db = self.dbbase.DB(':memory:')
        get_model_defaults = self.dbbase.utils.get_model_defaults

        class TestDefaults(db.Model):
            __tablename__ = "test_default"

            id = db.Column(db.Integer, primary_key=True)

            # model defaults - explicit values
            name = db.Column(db.String, default="string default", nullable=False)
            another_id = db.Column(db.SmallInteger, default=100)

            # model default - a function
            created_at1 = db.Column(db.DateTime, default=datetime.now)

            # server default
            created_at2 = db.Column(db.DateTime, server_default=db.func.now())

            # model default - but only updates - should not be included
            update_time1 = db.Column(db.DateTime, onupdate=datetime.now())

            # server default - but only updates - should not be included
            update_time2 = db.Column(
                db.DateTime, server_onupdate=db.func.now()
            )

        db.create_all()

        defaults = get_model_defaults(TestDefaults)

        self.assertSetEqual(
            set(['name', 'another_id', 'created_at1']),
            set(defaults.keys())
        )

        self.assertEqual(defaults['another_id'], 100)
        self.assertIsInstance(defaults['created_at1'], datetime)

# tests/test_dbbase/column_types.py
"""
This module tests column types.
"""
from . import DBBaseTestCase


class TestColumnTypes(DBBaseTestCase):
    """This class tests column type."""

    def test_create_write_only_column(self):
        """
        This function tests the creation of a write-only column.
        """
        db = self.db

        write_only_col = db.WriteOnlyColumn(db.String(50))

        self.assertIsInstance(write_only_col, db.Column)
        self.assertIsInstance(write_only_col, db.WriteOnlyColumn)

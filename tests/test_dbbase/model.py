# tests/test_dbbase/model.py
from . import DBBaseTestCase
from datetime import date, datetime


class TestModelClass(DBBaseTestCase):
    """This class test model features."""

    def test_create_model(self):
        """
        This function tests the creation of a simple model.
        """

        db = self.db

        class Table1(db.Model):
            __tablename__ = 'table1'

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)
            another_id = db.Column(db.SmallInteger)
            start_date = db.Column(db.Date, default=date.today)
            update_time = db.Column(db.DateTime, default=datetime.now)

        Table1.__table__.create(db.session.bind)

        table1_rec = Table1(
            # id=1,
            name='this is table1',
            another_id=4
            # letting defaults for start_date and update_time through
            )

        db.session.add(table1_rec)
        db.session.commit()

        self.assertIsNotNone(table1_rec)
        self.assertEqual(table1_rec.name, 'this is table1')
        self.assertEqual(table1_rec.another_id, 4)
        self.assertEqual(table1_rec.start_date, date.today())
        self.assertIsInstance(table1_rec.update_time, datetime)

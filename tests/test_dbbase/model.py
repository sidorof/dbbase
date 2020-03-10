# tests/test_dbbase/model.py
from . import DBBaseTestCase
from datetime import date, datetime


class TestModelClass(DBBaseTestCase):
    """This class test model features."""

    def test_create_model(self):
        """
        This function tests the creation of a simple model.
        """
        print('running test_create_model')
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

    def test_relationships(self):
        """This function tests relationships between tables."""
        db = self.db

        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)


        class Address(db.Model):
            __tablename__ = 'addresses'
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

            user = db.relationship("User", back_populates="addresses")

        User.addresses = db.relationship(
            "Address", back_populates="user")
            #"Address", order_by='Address.id', back_populates="user")

        User.metadata.create_all(db.session.bind)
        #Address.__table__.create(db.session.bind)


        #db.Model().metadata.create_all(engine, checkfirst=checkfirst)

        user = User(name='Bob')
        db.session.add(user)
        db.session.commit()

        address1 = Address(
            email_address='email1@example.com',
            user_id=user.id
        )
        address2 = Address(
            email_address='email2@example.com',
            user_id=user.id
        )

        db.session.add(address1)
        db.session.add(address2)
        db.session.commit()

        print('user.addresses', user.addresses)
        print('there are ', len(user.addresses), 'addresses')
        print('--------------------------')
        print('address1.serialize()', address1.serialize())
        print('address2.serialize()', address2.serialize())
        print()
        print('user.serialize()', user.serialize())

        print('db.config', db.config)











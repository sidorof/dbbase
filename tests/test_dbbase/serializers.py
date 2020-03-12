# tests/test_dbbase/serializers.py
from . import DBBaseTestCase
from datetime import date, datetime
from decimal import Decimal

import json
from random import randint


def init_variables(obj):

    obj.class_name = 'test_class'
    obj.to_camel_case = True
    obj.level_limits = None


class TestSerializers(DBBaseTestCase):

    #def test_eval_value_basic(self):
        #"""Test _eval_value

        #easy values
        #"""
        #_eval_value = self.dbbase.serializers._eval_value

        #init_variables(self)

        #value = 1
        #self.assertEqual(
            #value,
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))

        #value = 'this is text'
        #self.assertEqual(
            #value,
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))

        #value = 'this is text'
        #self.assertEqual(
            #value,
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))

        #value = datetime(2020, 7, 24, 12, 31, 5)
        #self.assertEqual(
            #'2020-07-24 12:31:05',
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))

        #value = date(2020, 7, 24)
        #self.assertEqual(
            #'2020-07-24',
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))

        #value = 123.456
        #self.assertAlmostEqual(
            #123.456,
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))

        #value = Decimal('123.456')
        #self.assertEqual(
            #'123.456',
            #_eval_value(
                #value, self.class_name, self.to_camel_case, self.level_limits))


    #def test_eval_value_model(self):
        #"""Test _eval_value

        #model values
        #"""
        #_eval_value = self.dbbase.serializers._eval_value

        #db = self.db

        #class User(db.Model):
            #__tablename__ = 'users'
            #id = db.Column(db.Integer, primary_key=True)
            #name = db.Column(db.String(30), nullable=False)
            #start_date = db.Column(db.Date, nullable=False)

        #User.metadata.create_all(db.session.bind)

        #user_id = 10032
        #user = User(
            #id=user_id,   # some arbitrary number
            #name='Bob',
            #start_date=date(2020, 3, 29))

        #db.session.add(user)
        #db.session.commit()
        #db.session.refresh(user)
        #init_variables(self)

        #value = user
        #self.assertDictEqual(
            #{
                #'id': 10032,
                #'name': 'Bob',
                #'startDate': '2020-03-29'
            #},
            #_eval_value(
                #value,
                #self.class_name,
                #self.to_camel_case,
                #self.level_limits))

        ## not camel case
        #self.assertDictEqual(
            #{
                #'id': 10032,
                #'name': 'Bob',
                #'start_date': '2020-03-29'
            #},
            #_eval_value(
                #value,
                #class_name=self.class_name,
                #to_camel_case=False,
                #level_limits=self.level_limits))


    def test_eval_value_model_relationships(self):
        """Test test_eval_value_model_relationships

        model values that get a relationship
        """
        _eval_value = self.dbbase.serializers._eval_value

        db = self.db

        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship("Address", backref="users", lazy='immediate')


        class Address(db.Model):
            __tablename__ = 'addresses'
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

            user = db.relationship("User", back_populates="addresses")

        User.addresses = db.relationship(
            "Address", back_populates="user", lazy='immediate')

        User.metadata.create_all(db.session.bind)

        user = User(
            id=randint(1, 1000000),
            name='Bob')

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

        db.session.refresh(user)
        db.session.refresh(address1)
        db.session.refresh(address2)
        init_variables(self)

        value = address1
        self.assertDictEqual(
            {
                'id': 1,
                'emailAddress': 'email1@example.com',
                'userId': user.id
            },
            address1.to_dict()
        )

        value = user
        self.assertDictEqual(
            {
                'id': user.id,
                'name': 'Bob',
                'addresses': [
                    {
                        'id': 1,
                        'emailAddress': 'email1@example.com',
                        'userId': user.id
                    },
                    {
                        'id': 2,
                        'emailAddress': 'email2@example.com',
                        'userId': user.id
                    }
                ]
            },
            _eval_value(
                value,
                self.class_name,
                self.to_camel_case,
                level_limits=set(['user']))
            )

    next do test that looks at adjacency list test_eval_value_model_relationships
    test break out separate test for _eval_value_list

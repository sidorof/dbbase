# tests/test_dbbase/model.py
"""
This module tests model functions.
"""
from datetime import date, datetime
from sqlalchemy.orm.relationships import RelationshipProperty

from . import DBBaseTestCase


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

    def test_relationships(self):
        """This function tests relationships between tables."""
        db = self.db

        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="user", lazy='immediate')

        class Address(db.Model):
            __tablename__ = 'addresses'
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

        User.metadata.create_all(db.session.bind)

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

        self.assertDictEqual(
            {
                "id": 1,
                "emailAddress": "email1@example.com",
                "userId": 1,
                "user": { "id": user.id, "name": "Bob"}
            },
            address1.to_dict()
        )

        self.assertDictEqual(
            {
                "id": 1,
                "name": "Bob",
                "addresses": [
                    {
                    "userId": 1,
                    "emailAddress": "email1@example.com",
                    "id": 1
                    },
                    {
                    "userId": 1,
                    "emailAddress": "email2@example.com",
                    "id": 2
                    }
                ]
            },
            user.to_dict()
        )

    def test_relationship_funcs_no_relations(self):
        """test_relationship_funcs_no_relations"""
        db = self.db

        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)

        User.metadata.create_all(db.session.bind)

        user = User(id=1, name='testname')
        db.session.add(user)
        db.session.commit()

        self.assertSetEqual(
            set(['id', 'name']), set(user.get_serial_field_list())
        )

        self.assertFalse(user._has_self_ref())

        # specific to fields
        self.assertIsNone(user._get_relationship(user.id))
        self.assertIsNone(user._get_relationship(user.name))

    def test_relationship_funcs_no_self_relation(self):
        """test_relationship_funcs_no_relations"""
        db = self.db

        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="user", lazy='immediate')


        class Address(db.Model):
            __tablename__ = 'addresses'
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

        User.metadata.create_all(db.session.bind)

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

        self.assertSetEqual(
            set(['id', 'name', 'addresses']),
            set(user.get_serial_field_list())
        )

        # specific to fields
        self.assertIsNone(user._get_relationship('id'))
        self.assertIsNone(user._get_relationship('name'))
        self.assertIsInstance(
            user._get_relationship('addresses'),
            RelationshipProperty
        )

        self.assertDictEqual(
            {
                'self-referential': False,
                'uselist': True,
                'join_depth': None
            },
            user._relations_info('addresses')
        )

        self.assertFalse(user._has_self_ref())

    def test_relationship_funcs_with_self_relation(self):
        """test_relationship_funcs_with_self_relation"""

        db = self.db

        class Node(db.Model):
            __tablename__ = 'nodes'
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey('nodes.id'))
            data = db.Column(db.String(50))
            children = db.relationship(
                "Node",
                lazy="joined",
                join_depth=10)

        Node.metadata.create_all(db.session.bind)

        node1 = Node(id=1, data='this is node1')
        node2 = Node(id=2, data='this is node2')
        node3 = Node(id=3, data='this is node3')
        node4 = Node(id=4, data='this is node4')
        node5 = Node(id=5, data='this is node5')
        node6 = Node(id=6, data='this is node6')

        db.session.add(node1)
        db.session.commit()
        node1.children.append(node2)
        db.session.commit()
        node2.children.append(node3)
        db.session.commit()
        #node2.children.append(node4)
        #db.session.commit()
        #node1.children.append(node5)
        #db.session.commit()
        #node5.children.append(node6)
        #db.session.commit()

        self.assertSetEqual(
            set(['id', 'parent_id', 'data', 'children']),
            set(node2.get_serial_field_list())
        )

        # specific to fields
        self.assertIsNone(node2._get_relationship('id'))
        self.assertIsNone(node2._get_relationship('parent_id'))
        self.assertIsNone(node2._get_relationship('data'))

        self.assertDictEqual(
            {
                'self-referential': True,
                'uselist': True,
                'join_depth': 10
            },
            node2._relations_info('children')
        )

        self.assertTrue(node2._has_self_ref())

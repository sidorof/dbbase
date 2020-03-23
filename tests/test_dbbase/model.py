# tests/test_dbbase/model.py
"""
This module tests model functions.
"""
from datetime import date, datetime
import json
from collections import OrderedDict
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
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)
            another_id = db.Column(db.SmallInteger)
            start_date = db.Column(db.Date, default=date.today)
            update_time = db.Column(db.DateTime, default=datetime.now)

        db.create_all()

        table1_rec = Table1(
            # id=1,
            name="this is table1",
            another_id=4
            # letting defaults for start_date and update_time through
        )

        db.session.add(table1_rec)
        db.session.commit()

        self.assertIsNotNone(table1_rec)
        self.assertEqual(table1_rec.name, "this is table1")
        self.assertEqual(table1_rec.another_id, 4)
        self.assertEqual(table1_rec.start_date, date.today())
        self.assertIsInstance(table1_rec.update_time, datetime)

    def test_relationships(self):
        """This function tests relationships between tables."""
        db = self.db

        class User(db.Model):
            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="user", lazy="immediate"
            )

        class Address(db.Model):
            __tablename__ = "addresses"
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

        db.create_all()

        user = User(name="Bob")
        db.session.add(user)
        db.session.commit()

        address1 = Address(email_address="email1@example.com", user_id=user.id)
        address2 = Address(email_address="email2@example.com", user_id=user.id)

        db.session.add(address1)
        db.session.add(address2)
        db.session.commit()

        self.assertDictEqual(
            {
                "id": 1,
                "emailAddress": "email1@example.com",
                "userId": 1,
                "user": {"id": user.id, "name": "Bob"},
            },
            address1.to_dict(),
        )

        self.assertDictEqual(
            {
                "id": 1,
                "name": "Bob",
                "addresses": [
                    {
                        "userId": 1,
                        "emailAddress": "email1@example.com",
                        "id": 1,
                    },
                    {
                        "userId": 1,
                        "emailAddress": "email2@example.com",
                        "id": 2,
                    },
                ],
            },
            user.to_dict(),
        )

    def test_relationship_funcs_no_relations(self):
        """test_relationship_funcs_no_relations"""
        db = self.db

        class User(db.Model):
            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)

        db.create_all()

        user = User(id=1, name="testname")
        db.session.add(user)
        db.session.commit()

        self.assertSetEqual(
            set(["id", "name"]), set(user.get_serial_field_list())
        )

        self.assertFalse(user._has_self_ref())

        # specific to fields
        self.assertIsNone(user._get_relationship(user.id))
        self.assertIsNone(user._get_relationship(user.name))

    def test_relationship_funcs_no_self_relation(self):
        """test_relationship_funcs_no_relations"""
        db = self.db

        class User(db.Model):
            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="user", lazy="immediate"
            )

        class Address(db.Model):
            __tablename__ = "addresses"
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

        db.create_all()

        user = User(name="Bob")
        db.session.add(user)
        db.session.commit()

        address1 = Address(email_address="email1@example.com", user_id=user.id)
        address2 = Address(email_address="email2@example.com", user_id=user.id)

        db.session.add(address1)
        db.session.add(address2)
        db.session.commit()

        self.assertSetEqual(
            set(["id", "name", "addresses"]), set(user.get_serial_field_list())
        )

        # specific to fields
        self.assertIsNone(user._get_relationship("id"))
        self.assertIsNone(user._get_relationship("name"))
        self.assertIsInstance(
            user._get_relationship("addresses"), RelationshipProperty
        )

        self.assertDictEqual(
            {"self-referential": False, "uselist": True, "join_depth": None},
            user._relations_info("addresses"),
        )

        self.assertFalse(user._has_self_ref())

    def test_relationship_funcs_with_self_relation(self):
        """test_relationship_funcs_with_self_relation"""

        db = self.db

        class Node(db.Model):
            __tablename__ = "nodes"
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey("nodes.id"))
            data = db.Column(db.String(50))
            children = db.relationship("Node", lazy="joined", join_depth=10)

        db.create_all()

        node1 = Node(id=1, data="this is node1")
        node2 = Node(id=2, data="this is node2")
        node3 = Node(id=3, data="this is node3")

        db.session.add(node1)
        db.session.commit()
        node1.children.append(node2)
        db.session.commit()
        node2.children.append(node3)
        db.session.commit()

        self.assertSetEqual(
            set(["id", "parent_id", "data", "children"]),
            set(node2.get_serial_field_list()),
        )

        # specific to fields
        self.assertIsNone(node2._get_relationship("id"))
        self.assertIsNone(node2._get_relationship("parent_id"))
        self.assertIsNone(node2._get_relationship("data"))

        self.assertDictEqual(
            {"self-referential": True, "uselist": True, "join_depth": 10},
            node2._relations_info("children"),
        )

        self.assertTrue(node2._has_self_ref())

    def test_query(self):
        """"test_query"""
        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(name="test").save()

        self.assertEqual(table1.id, Table1.query.get(1).id)

    def test__class(self):
        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)

        class Table2(db.Model):
            __tablename__ = "table2"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(name="test").save()
        table2 = Table2(name="test").save()

        self.assertEqual("table1", table1._class())
        self.assertEqual("table2", table2._class())

    def test__get_serial_stop_list(self):
        """Test get_serial_stop_list """

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)

        db.create_all()

        Table1.SERIAL_STOPLIST = "potato"

        self.assertRaises(ValueError, Table1._get_serial_stop_list)

        # does SERIAL_STOPLIST get screened?
        Table1.SERIAL_STOPLIST = ["potato"]

        self.assertIn("potato", Table1._get_serial_stop_list())

    def test__get_relationship_none(self):
        """test__get_relationship_none"""

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(name="test").save()

        self.assertIsNone(table1._get_relationship("name"))

    def test__get_relationship_valid(self):
        """test__get_relationship_valid"""

        db = self.db

        class User(db.Model):
            """simple table"""

            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="user", lazy="immediate"
            )

        class Address(db.Model):
            """related table"""

            __tablename__ = "addresses"
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

        db.create_all()

        user = User(name="Bob").save()

        self.assertIsInstance(
            user._get_relationship("addresses"), RelationshipProperty
        )

    def test__relations_info(self):
        """test__relations_info"""
        db = self.db

        class User(db.Model):
            """simple table"""

            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="user", lazy="immediate"
            )

        class Address(db.Model):
            """related table"""

            __tablename__ = "addresses"
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

        db.create_all()

        user = User(name="Bob").save()

        # really only care if 'self-referential' True or False
        self.assertDictEqual(
            {"self-referential": False, "uselist": True, "join_depth": None},
            user._relations_info("addresses"),
        )

    def test__has_self_ref(self):
        db = self.db

        # non-self-referential
        class User(db.Model):
            """simple table"""

            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)

        # self-referential
        class Node(db.Model):
            """self-referential table"""

            __tablename__ = "nodes"
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey("nodes.id"))
            data = db.Column(db.String(50))
            children = db.relationship(
                "Node", lazy="joined", order_by="Node.id", join_depth=10
            )

        db.create_all()

        user1 = User(name="bob").save()
        node1 = Node(id=1, data="this is node1").save()

        self.assertFalse(user1._has_self_ref())
        self.assertTrue(node1._has_self_ref())

    def test_get_serial_field_list(self):
        db = self.db

        class Node(db.Model):
            """self-referential table"""

            __tablename__ = "nodes"
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey("nodes.id"))
            data = db.Column(db.String(50))
            children = db.relationship(
                "Node", lazy="joined", order_by="Node.id", join_depth=10
            )

        db.create_all()

        node1 = Node(id=1, data="this is node1").save()
        # since don't care about order, use set
        self.assertSetEqual(
            set(["id", "parent_id", "data", "children"]),
            set(node1.get_serial_field_list()),
        )

    def test_to_dict(self):
        db = self.db

        class Node(db.Model):
            """self-referential table"""

            __tablename__ = "nodes"
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey("nodes.id"))
            data = db.Column(db.String(50))
            children = db.relationship(
                "Node", lazy="joined", order_by="Node.id", join_depth=10
            )

        db.create_all()

        node1 = Node(id=1, data="this is node1")
        node2 = Node(id=2, data="this is node2")
        node3 = Node(id=3, data="this is node3")

        db.session.add(node1)
        db.session.commit()
        node1.children.append(node2)
        db.session.commit()
        node2.children.append(node3)
        db.session.commit()

        # to be tested
        #   (not level_limits=None since that is really an internal process)

        self.assertDictEqual(
            {
                "data": "this is node1",
                "children": [
                    {
                        "data": "this is node2",
                        "children": [
                            {
                                "data": "this is node3",
                                "children": [],
                                "parentId": 2,
                                "id": 3,
                            }
                        ],
                        "parentId": 1,
                        "id": 2,
                    }
                ],
                "parentId": None,
                "id": 1,
            },
            node1.to_dict(to_camel_case=True, sort=False),
        )

        # check defaults
        self.assertDictEqual(
            node1.to_dict(), node1.to_dict(to_camel_case=True, sort=False)
        )

        # no camel case conversion
        self.assertDictEqual(
            {
                "parent_id": None,
                "id": 1,
                "data": "this is node1",
                "children": [
                    {
                        "parent_id": 1,
                        "id": 2,
                        "data": "this is node2",
                        "children": [
                            {
                                "parent_id": 2,
                                "id": 3,
                                "data": "this is node3",
                                "children": [],
                            }
                        ],
                    }
                ],
            },
            node1.to_dict(to_camel_case=False, sort=False),
        )

        # sorted alphabetical order
        self.assertDictEqual(
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [],
                                "id": 3,
                                "data": "this is node3",
                                "parentId": 2,
                            }
                        ],
                        "id": 2,
                        "data": "this is node2",
                        "parentId": 1,
                    }
                ],
                "data": "this is node1",
                "id": 1,
                "parentId": None,
            },
            node1.to_dict(to_camel_case=True, sort=True),
        )

        # sorted in the order of Serial list
        Node.SERIAL_LIST = ["id", "parent_id", "data", "children"]

        self.assertEqual(
            str(
                OrderedDict(
                    {
                        "id": 1,
                        "parentId": None,
                        "data": "this is node1",
                        "children": [
                            {
                                "id": 2,
                                "parentId": 1,
                                "data": "this is node2",
                                "children": [
                                    {
                                        "id": 3,
                                        "parentId": 2,
                                        "data": "this is node3",
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    }
                )
            ),
            str(OrderedDict(node1.to_dict(to_camel_case=True, sort=False))),
        )

    def test_serialize(self):
        """test_serialize"""

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            long_name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(long_name="this is a long name").save()

        self.assertEqual(
            json.dumps(table1.to_dict(to_camel_case=True, sort=False)),
            table1.serialize(to_camel_case=True, sort=False),
        )

        self.assertEqual(
            json.dumps(table1.to_dict(to_camel_case=False, sort=False)),
            table1.serialize(to_camel_case=False, sort=False),
        )

        # test both sort and indent
        self.assertEqual(
            json.dumps(
                table1.to_dict(to_camel_case=False, sort=True), indent=4
            ),
            table1.serialize(to_camel_case=False, sort=True, indent=4),
        )

    def test_deserialize(self):
        """test_deserialize"""

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            long_name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(long_name="this is a long name").save()

        data = {"id": 1, "longName": "this is a long name"}

        self.assertDictEqual(
            {"id": 1, "long_name": "this is a long name"},
            table1.deserialize(data, from_camel_case=True),
        )
        self.assertDictEqual(
            {"id": 1, "longName": "this is a long name"},
            table1.deserialize(data, from_camel_case=False),
        )

        data = json.dumps(
            [
                {"id": 3, "longName": "this is a long name"},
                {"id": 4, "longName": "this is a long name"},
            ]
        )

        self.assertListEqual(
            [
                {"id": 3, "long_name": "this is a long name"},
                {"id": 4, "long_name": "this is a long name"},
            ],
            table1.deserialize(data, from_camel_case=True),
        )

    def test_save(self):
        """test_save"""

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            long_name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(long_name="this is a long name")

        self.assertIsNone(table1.id)

        table_saved = table1.save()

        self.assertIsNotNone(table1.id)

        self.assertEqual(table1, table_saved)

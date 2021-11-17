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

    def test__null_columns(self):
        """test__null_columns

        This function tests the _null_columns function for missing
        values.
        """
        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String, nullable=False)
            start_date = db.Column(db.Date, default=date.today)
            created_at1 = db.Column(db.DateTime, default=datetime.now)
            created_at2 = db.Column(db.DateTime, server_default=db.func.now())
            update_time1 = db.Column(db.DateTime, onupdate=datetime.now())
            update_time2 = db.Column(
                db.DateTime, server_onupdate=db.func.now()
            )

            # adapted from sqlalchemy docs
            abc = db.Column(db.String(20), server_default="abc")
            index_value = db.Column(db.Integer, server_default=db.text("0"))

        db.create_all()

        table1_rec = Table1(name="test")

        self.assertListEqual(
            table1_rec._null_columns(),
            [
                "id",
                "start_date",
                "created_at1",
                "created_at2",
                "update_time1",
                "update_time2",
                "abc",
                "index_value",
            ],
        )

    def test_validate_record(self):
        """
        This function tests whether missing values can be found
        prior to attempting to save.
        """
        db = self.db

        # a table with various kinds of default values
        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            first_name = db.Column(db.String, nullable=False)
            last_name = db.Column(db.String, nullable=False)
            start_date = db.Column(db.Date, default=date.today)
            created_at1 = db.Column(db.DateTime, default=datetime.now)
            created_at2 = db.Column(db.DateTime, server_default=db.func.now())
            update_time1 = db.Column(db.DateTime, onupdate=datetime.now())
            update_time2 = db.Column(
                db.DateTime, server_onupdate=db.func.now()
            )

            # adapted from sqlalchemy docs
            abc = db.Column(db.String(20), server_default="abc")
            index_value = db.Column(db.Integer, server_default=db.text("0"))

            fk_id = db.Column(
                db.Integer, db.ForeignKey("table2.id"), nullable=False
            )

            fk_name = db.Column(
                db.String, db.ForeignKey("table3.name"), nullable=False
            )

        class Table2(db.Model):
            __tablename__ = "table2"
            id = db.Column(db.Integer, primary_key=True)

        class Table3(db.Model):
            __tablename__ = "table3"
            name = db.Column(db.String, primary_key=True)

        db.create_all()

        table1_rec = Table1(
            # id filled in by server
            first_name="Bob",
            # last_name skipped to test the function
            # start_date has local default
            # created_at1 has local default
            # created_at2 has server default
            # update_time1 has local default, but only on update
            # update_time2 has server default, but only on update
            fk_name="test",
        )

        table3_rec = Table3(name="test").save()

        self.assertDictEqual(
            table1_rec._extract_foreign_keys(),
            {
                "fk_id": {"foreign_key": "table2.id"},
                "fk_name": {"foreign_key": "table3.name"},
            },
        )

        # default
        status, errors = table1_rec.validate_record()

        self.assertFalse(status)
        self.assertDictEqual(
            errors, {"missing_values": ["last_name", "fk_id"]}
        )

        # camel_case
        status, errors = table1_rec.validate_record(camel_case=True)

        self.assertFalse(status)
        self.assertDictEqual(errors, {"missingValues": ["lastName", "fkId"]})

        table1_rec.last_name = "name is filled in"
        table1_rec.fk_id = 3  # not a valid fk

        status, errors = table1_rec._validate_foreignkeys()

        self.assertFalse(status)
        self.assertListEqual(
            errors, [{"fk_id": "3 is not a valid foreign key"}]
        )

        status, errors = table1_rec.validate_record()

        self.assertFalse(status)
        self.assertDictEqual(
            errors,
            {"ForeignKeys": [{"fk_id": "3 is not a valid foreign key"}]},
        )
        table2_rec = Table2(id=3).save()
        status, errors = table1_rec.validate_record()

        self.assertTrue(status)
        self.assertIsNone(errors)

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
            address1.to_dict(),
            {
                "id": 1,
                "emailAddress": "email1@example.com",
                "userId": 1,
                "user": {"id": user.id, "name": "Bob"},
            },
        )

        self.assertDictEqual(
            user.to_dict(),
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

        self.assertSetEqual(set(["id", "name"]), set(user.get_serial_fields()))

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
            set(user.get_serial_fields()), set(["id", "name", "addresses"])
        )

        # specific to fields
        self.assertIsNone(user._get_relationship("id"))
        self.assertIsNone(user._get_relationship("name"))
        self.assertIsInstance(
            user._get_relationship("addresses"), RelationshipProperty
        )

        self.assertDictEqual(
            user._relations_info("addresses"),
            {
                "self-referential": False,
                "uselist": True,
                "join_depth": None,
                "lazy": "immediate",
                "bidirectional": True,
            },
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
            set(node2.get_serial_fields()),
            set(["id", "parent_id", "data", "children"]),
        )

        # specific to fields
        self.assertIsNone(node2._get_relationship("id"))
        self.assertIsNone(node2._get_relationship("parent_id"))
        self.assertIsNone(node2._get_relationship("data"))

        self.assertDictEqual(
            node2._relations_info("children"),
            {
                "self-referential": True,
                "uselist": True,
                "join_depth": 10,
                "lazy": "joined",
                "bidirectional": False,
            },
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

        self.assertEqual("Table1", table1._class())
        self.assertEqual("Table2", table2._class())

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
            role_id = db.Column(
                db.Integer, db.ForeignKey("roles.id"), nullable=False
            )
            role = db.relationship("Role")

        class Address(db.Model):
            """related table"""

            __tablename__ = "addresses"
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

        class Role(db.Model):
            """ related but not bidirectional

            pretend there can only be one role
            """

            __tablename__ = "roles"
            id = db.Column(db.Integer, primary_key=True)
            role = db.Column(db.String, nullable=False)

        db.create_all()
        role = Role(role="staff").save()
        user = User(name="Bob", role_id=role.id).save()

        self.assertDictEqual(
            user._relations_info("addresses"),
            {
                "self-referential": False,
                "uselist": True,
                "join_depth": None,
                "lazy": "immediate",
                "bidirectional": True,
            },
        )

        self.assertDictEqual(
            user._relations_info("role"),
            {
                "self-referential": False,
                "uselist": False,
                "join_depth": None,
                "lazy": "select",
                "bidirectional": False,
            },
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

    def test_get_serial_fields(self):
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
            set(node1.get_serial_fields()),
            set(["id", "parent_id", "data", "children"]),
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

            def test_func(self):
                """would be included in to_dict"""
                return "test_func"
            def test_func1(self, var1):
                """would not be included in to_dict"""
                return f"test_func:{var1}"
            def test_func2(self, var1, var2):
                """would not be included in to_dict"""
                return f"test_func: {var1}, {var2}"

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
            node1.to_dict(to_camel_case=True, sort=False),
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
                                "testFunc": "test_func",
                            }
                        ],
                        "parentId": 1,
                        "id": 2,
                        "testFunc": "test_func",
                    }
                ],
                "parentId": None,
                "id": 1,
                "testFunc": "test_func",
            },
        )

        # check defaults
        self.assertDictEqual(
            node1.to_dict(), node1.to_dict(to_camel_case=True, sort=False)
        )

        # no camel case conversion
        self.assertDictEqual(
            node1.to_dict(to_camel_case=False, sort=False),
            {
                "parent_id": None,
                "id": 1,
                "data": "this is node1",
                "test_func": "test_func",
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
                                "test_func": "test_func"
                            }
                        ],
                        "test_func": "test_func",
                    }
                ],
            },
        )

        # sorted alphabetical order
        self.assertDictEqual(
            node1.to_dict(to_camel_case=True, sort=True),
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [],
                                "id": 3,
                                "data": "this is node3",
                                "parentId": 2,
                                "testFunc": "test_func",

                            }
                        ],
                        "id": 2,
                        "data": "this is node2",
                        "parentId": 1,
                        "testFunc": "test_func",

                    }
                ],
                "data": "this is node1",
                "id": 1,
                "parentId": None,
                "testFunc": "test_func"
            },
        )

        # sorted in the order of serial fields
        Node.SERIAL_FIELDS = ["id", "parent_id", "data", "children"]

        self.assertEqual(
            str(OrderedDict(node1.to_dict(to_camel_case=True, sort=False))),
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
        )

        # test ad hoc serial list
        self.assertDictEqual(
            node1.to_dict(serial_fields=["parent_id"]), {"parentId": None},
        )

        # test ad hoc serial list with children
        # serial list should be only with parent not children
        #   since it is updating self rather than cls
        self.assertDictEqual(
            node1.to_dict(serial_fields=["id", "children"]),
            {
                "id": 1,
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
            },
        )

        # test serial list for relations not the parent
        # parent will be complete, children will be limited
        self.assertDictEqual(
            node1.to_dict(serial_field_relations={"Node": ["id", "children"]}),
            {
                "id": 1,
                "parentId": None,
                "data": "this is node1",
                "children": [
                    {"id": 2, "children": [{"id": 3, "children": []}]}
                ],
            },
        )
        # test both serial list and serial_field_relations
        # this is equivalent to having set the class SERIAL_FIELDS
        #   in the first place.
        self.assertDictEqual(
            node1.to_dict(
                serial_fields=["id", "children"],
                serial_field_relations={"Node": ["id", "children"]},
            ),
            {
                "id": 1,
                "children": [
                    {"id": 2, "children": [{"id": 3, "children": []}]}
                ],
            },
        )

    def test_to_dict_relationtype(self):
        """ test_to_dict_relationtype

        This function tests the ability to recognize the impact of
        dynamic relations on to_dict.

        The issue here is lazy dynamic
        """
        db = self.db

        class Table(db.Model):

            __tablename__ = "table"

            id = db.Column(db.Integer, primary_key=True)
            item_ones = db.relationship(
                "Table1", backref="table0", lazy="immediate"
            )

            item_twos = db.relationship(
                "Table2", backref="table0", lazy="dynamic"
            )

            item_threes = db.relationship("Table3", backref="table0")

            item_fours = db.relationship("Table4", backref="table0")

        class Table1(db.Model):

            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            table_id = db.Column(db.Integer, db.ForeignKey("table.id"))

        class Table2(db.Model):

            __tablename__ = "table2"

            id = db.Column(db.Integer, primary_key=True)
            table_id = db.Column(db.Integer, db.ForeignKey("table.id"))

        class Table3(db.Model):

            __tablename__ = "table3"

            id = db.Column(db.Integer, primary_key=True)
            table_id = db.Column(db.Integer, db.ForeignKey("table.id"))

        class Table4(db.Model):

            __tablename__ = "table4"

            id = db.Column(db.Integer, primary_key=True)
            table_id = db.Column(db.Integer, db.ForeignKey("table.id"))

        db.create_all()

        table = Table(id=0).save()
        table1 = Table1(id=1, table_id=0).save()
        table2 = Table2(id=2, table_id=0).save()
        table3 = Table3(id=3, table_id=0).save()
        table4 = Table4(id=4).save()
        # table 4 is skipped, so empty

        self.assertDictEqual(
            table.to_dict(),
            {
                "id": 0,
                "itemOnes": [{"tableId": 0, "id": 1}],
                "itemTwos": [{"tableId": 0, "id": 2}],
                "itemThrees": [{"tableId": 0, "id": 3}],
                "itemFours": [],
            },
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
            table1.serialize(to_camel_case=True, sort=False),
            json.dumps(table1.to_dict(to_camel_case=True, sort=False)),
        )

        self.assertEqual(
            table1.serialize(to_camel_case=False, sort=False),
            json.dumps(table1.to_dict(to_camel_case=False, sort=False)),
        )

        # test both sort and indent
        self.assertEqual(
            table1.serialize(to_camel_case=False, sort=True, indent=4),
            json.dumps(
                table1.to_dict(to_camel_case=False, sort=True), indent=4
            ),
        )

    def test_deserialize(self):
        """test_deserialize"""

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            long_name = db.Column(db.String, nullable=False)

            def another_method(self):
                if self.long_name is not None:
                    return self.long_name.capitalize()
                else:
                    return None

        db.create_all()

        table1 = Table1(long_name="this is a long name").save()

        data = {
            "id": 1,
            "longName": "this is a long name",
            # extraneous garbage
            "other": "This is a test",
            # data included in a serialization
            "anotherMethod": "This Is A Long Name",
        }

        self.assertDictEqual(
            table1.deserialize(data, from_camel_case=True),
            {
                "id": 1,
                "long_name": "this is a long name",
                "other": "This is a test",
                "another_method": "This Is A Long Name",
            },
        )

        self.assertDictEqual(
            table1.deserialize(data, from_camel_case=True, only_columns=True),
            {"id": 1, "long_name": "this is a long name"},
        )

        self.assertDictEqual(
            table1.deserialize(data, from_camel_case=False),
            {
                "id": 1,
                "longName": "this is a long name",
                "other": "This is a test",
                "anotherMethod": "This Is A Long Name",
            },
        )

        data = json.dumps(
            [
                {
                    "id": 3,
                    "longName": "this is a long name",
                    "other": "This is a test3",
                    "another_method": "This Is A Long Name",
                },
                {
                    "id": 4,
                    "longName": "this is a long name",
                    "other": "This is a test4",
                    "another_method": "This Is A Long Name",
                },
            ]
        )

        self.assertListEqual(
            table1.deserialize(data, from_camel_case=True),
            [
                {
                    "id": 3,
                    "long_name": "this is a long name",
                    "other": "This is a test3",
                    "another_method": "This Is A Long Name",
                },
                {
                    "id": 4,
                    "long_name": "this is a long name",
                    "other": "This is a test4",
                    "another_method": "This Is A Long Name",
                },
            ],
        )

        self.assertListEqual(
            table1.deserialize(data, from_camel_case=True, only_columns=True),
            [
                {"id": 3, "long_name": "this is a long name"},
                {"id": 4, "long_name": "this is a long name"},
            ],
        )

        # test for byte conversion
        data = json.dumps(
            [
                {"id": 3, "longName": "this is a long name"},
                {"id": 4, "longName": "this is a long name"},
            ]
        )
        self.assertIsInstance(data, str)

        data = data.encode()
        self.assertIsInstance(data, bytes)

        self.assertListEqual(
            table1.deserialize(data, from_camel_case=True),
            [
                {"id": 3, "long_name": "this is a long name"},
                {"id": 4, "long_name": "this is a long name"},
            ],
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

    def test_delete(self):
        """test_delete"""

        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            long_name = db.Column(db.String, nullable=False)

        db.create_all()

        table1 = Table1(long_name="this is a long name")

        table1.save()

        table_id = table1.id

        self.assertIsNotNone(table1.id)

        table1.delete()

        self.assertIsNone(Table1.query.get(table_id))

    def test__write_only_columns(self):
        """test__write_only_columns

        A write only column should appear in the serial list of fields
        if there is None. Otherwise, it should be excluded.

        The point of this is to never show a password field that
        has any information filled in, but be available if a password
        is needed.

        Also, tests for writable properties.

        """
        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"

            id = db.Column(db.Integer, primary_key=True)
            password = db.WriteOnlyColumn(db.String, nullable=False)

            def __init__(self, id=None, password=None, writable=None):
                self.id = id
                self.password = password
                self._writable = writable

            @property
            def writable(self) -> str:
                return self._writable

            @writable.setter
            def writable(self, text) -> str:
                self._writable(text)

            @property
            def not_writable(self) -> str:
                return "this is not writable"

        db.create_all()

        table1 = Table1()
        table2 = Table1(
            password="some encrypted value", writable="this is writable"
        )

        # test doc_table too
        self.assertDictEqual(
            db.doc_table(Table1),
            {
                "Table1": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int32",
                            "primary_key": True,
                            "nullable": False,
                            "info": {},
                        },
                        "password": {
                            "type": "string",
                            "nullable": False,
                            "info": {"writeOnly": True},
                        },
                        "writable": {
                            "property": True,
                            "readOnly": False,
                            "type": "str",
                        },
                        "not_writable": {
                            "property": True,
                            "readOnly": True,
                            "type": "str",
                        },
                    },
                    "xml": "Table1",
                }
            },
        )

        self.assertDictEqual(
            {
                "id": None,
                "password": None,
                "writable": None,
                "notWritable": "this is not writable",
             },
            table1.to_dict())

        self.assertDictEqual(
            {
                "id": None,
                "writable": "this is writable",
                "notWritable": "this is not writable",
             },
            table2.to_dict(),
        )

    def test_filter_columns(self):
        """ test_filter_columns

        This test should show selection by column prop
        type, options for output of the attributes and
        camel case.
        """
        db = self.db

        class Author(db.Model):
            __tablename__ = "authors"

            id = db.Column(db.Integer, primary_key=True)
            first_name = db.Column(db.String(50), nullable=False)
            last_name = db.Column(db.String(50), nullable=False)
            test_col = db.WriteOnlyColumn(db.String(50), nullable=True)

            def full_name(self):
                return f"{self.first_name} {self.last_name}"

            books = db.relationship("Book", backref="author", lazy="dynamic")

        class Book(db.Model):
            __tablename__ = "books"

            id = db.Column(db.Integer, primary_key=True, nullable=True)
            isbn = db.Column(db.String(20), nullable=True)
            title = db.Column(db.String(100))
            pub_year = db.Column(db.Integer, nullable=False)
            author_id = db.Column(
                db.Integer, db.ForeignKey("authors.id"), nullable=False
            )

        db.create_all()

        # select nullable
        doc = Book.filter_columns(
            column_props=["nullable"], to_camel_case=True, only_props=False
        )

        self.assertDictEqual(
            doc,
            {
                "id": {
                    "type": "integer",
                    "format": "int32",
                    "primary_key": True,
                    "nullable": True,
                    "info": {},
                },
                "isbn": {
                    "type": "string",
                    "maxLength": 20,
                    "nullable": True,
                    "info": {},
                },
                "title": {
                    "type": "string",
                    "maxLength": 100,
                    "nullable": True,
                    "info": {},
                },
            },
        )

        # select foreign_keys
        doc = Book.filter_columns(
            column_props=["foreign_key"], to_camel_case=True, only_props=True
        )

        self.assertDictEqual(doc, {"authorId": {"foreign_key": "authors.id"}})

        # select not read only
        doc = Book.filter_columns(
            column_props=["!readOnly"], to_camel_case=True, only_props=False
        )
        self.assertDictEqual(
            doc,
            {
                "id": {
                    "type": "integer",
                    "format": "int32",
                    "primary_key": True,
                    "nullable": True,
                    "info": {},
                },
                "isbn": {
                    "type": "string",
                    "maxLength": 20,
                    "nullable": True,
                    "info": {},
                },
                "title": {
                    "type": "string",
                    "maxLength": 100,
                    "nullable": True,
                    "info": {},
                },
                "pubYear": {
                    "type": "integer",
                    "format": "int32",
                    "nullable": False,
                    "info": {},
                },
                "authorId": {
                    "type": "integer",
                    "format": "int32",
                    "nullable": False,
                    "foreign_key": "authors.id",
                    "info": {},
                },
            },
        )

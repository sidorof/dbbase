# tests/test_dbbase/serializers.py
"""
This module tests various aspects of serialization.
"""
from datetime import date, datetime
from decimal import Decimal
from random import randint

from . import DBBaseTestCase


def init_variables(obj):
    """common variables"""
    obj.to_camel_case = True
    obj.level_limits = set()


class TestSerializers(DBBaseTestCase):
    """Test class for serializers """

    def test_eval_value_basic(self):
        """Test _eval_value

        easy values
        """
        _eval_value = self.dbbase.serializers._eval_value

        init_variables(self)

        value = 1
        self.assertEqual(
            value,
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

        value = "this is text"
        self.assertEqual(
            value,
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

        value = "this is text"
        self.assertEqual(
            value,
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

        value = datetime(2020, 7, 24, 12, 31, 5)
        self.assertEqual(
            "2020-07-24 12:31:05",
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

        value = date(2020, 7, 24)
        self.assertEqual(
            "2020-07-24",
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

        value = 123.456
        self.assertAlmostEqual(
            123.456,
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

        value = Decimal("123.456")
        self.assertEqual(
            "123.456",
            _eval_value(value, self.to_camel_case, self.level_limits, None),
        )

    def test_eval_value(self):
        """Test _eval_value

        model values

        The scenario for this testing is that the model has been routed
        to it as part of a larger process. So, the test here narrowly
        evaluates:
            is the model in level_limits, i.e. already been processed?
            if so, is the model self-referential, so should it be
            processed again?

        In this case, the model is not self-referential.
        """
        _eval_value = self.dbbase.serializers._eval_value

        db = self.db

        class User(db.Model):
            """simple table"""

            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            start_date = db.Column(db.Date, nullable=False)

        db.create_all()

        user_id = 10032
        user = User(
            id=user_id,  # some arbitrary number
            name="Bob",
            start_date=date(2020, 3, 29),
        )

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        value = user
        self.assertDictEqual(
            {"id": 10032, "name": "Bob", "startDate": "2020-03-29"},
            _eval_value(
                value,
                to_camel_case=True,
                level_limits=set(),
                source_class=None,
            ),
        )

        # not camel case
        self.assertDictEqual(
            {"id": 10032, "name": "Bob", "start_date": "2020-03-29"},
            _eval_value(
                value,
                to_camel_case=False,
                level_limits=set(),
                source_class=None,
            ),
        )

        # model has been already processed, so level_limits has class
        level_limits = set()
        level_limits.add(user._class())
        self.assertEqual(
            self.dbbase.serializers.STOP_VALUE,
            _eval_value(
                value,
                to_camel_case=False,
                level_limits=level_limits,
                source_class=value._class(),
            ),
        )

    def test_eval_value_model_relationships(self):
        """Test test_eval_value_model_relationships

        model values that get a relationship
        """
        _eval_value = self.dbbase.serializers._eval_value

        db = self.db

        class User(db.Model):
            """base table"""

            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)
            addresses = db.relationship(
                "Address", backref="users", lazy="immediate"
            )

        class Address(db.Model):
            """related table"""

            __tablename__ = "addresses"
            id = db.Column(db.Integer, primary_key=True)
            email_address = db.Column(db.String, nullable=False)
            user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

            user = db.relationship("User", back_populates="addresses")

        User.addresses = db.relationship(
            "Address", back_populates="user", lazy="immediate"
        )

        db.create_all()

        user = User(id=randint(1, 1000000), name="Bob")

        db.session.add(user)
        db.session.commit()

        address1 = Address(email_address="email1@example.com", user_id=user.id)
        address2 = Address(email_address="email2@example.com", user_id=user.id)

        db.session.add(address1)
        db.session.add(address2)
        db.session.commit()

        db.session.refresh(user)
        db.session.refresh(address1)
        db.session.refresh(address2)

        value = address1
        level_limits = set()
        # starts from no source_class, so does address => user, then stops
        self.assertDictEqual(
            {
                "id": 1,
                "emailAddress": "email1@example.com",
                "userId": user.id,
                "user": {"id": user.id, "name": "Bob"},
            },
            _eval_value(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )

        value = user
        level_limits = set()

        self.assertDictEqual(
            {
                "id": user.id,
                "name": "Bob",
                "addresses": [
                    {
                        "id": 1,
                        "emailAddress": "email1@example.com",
                        "userId": user.id,
                    },
                    {
                        "id": 2,
                        "emailAddress": "email2@example.com",
                        "userId": user.id,
                    },
                ],
            },
            _eval_value(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )

    def test_eval_value_list(self):
        """Test test_eval_value_list

        """
        _eval_value_list = self.dbbase.serializers._eval_value_list

        db = self.db

        class User(db.Model):
            """simple table"""

            __tablename__ = "users"
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(30), nullable=False)

        db.create_all()

        user1 = User(id=randint(1, 1000000), name="Bob")

        user2 = User(id=randint(1, 1000000), name="JimBob")

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        db.session.refresh(user1)
        db.session.refresh(user2)

        value = ["something", "trivial"]
        level_limits = set()
        self.assertTupleEqual(
            (["something", "trivial"], level_limits),
            _eval_value_list(
                value,
                to_camel_case=True,
                level_limits=set(),
                source_class=None,
            ),
        )

        value = [user1, user2]
        level_limits = set()

        self.assertTupleEqual(
            (
                [
                    {"id": user1.id, "name": "Bob"},
                    {"id": user2.id, "name": "JimBob"},
                ],
                set([user1._class()]),
            ),
            _eval_value_list(
                value,
                to_camel_case=True,
                level_limits=set(),
                source_class=None,
            ),
        )

    def test_eval_value_model(self):
        """Test test_eval_value_model

        This test focusses on a few things:
        Recognize a model
        Respond properly to a level_limits

        model values that get a relationship
        """
        _eval_value_model = self.dbbase.serializers._eval_value_model

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

        user = User(id=randint(1, 1000000), name="Bob")

        db.session.add(user)
        db.session.commit()

        address1 = Address(email_address="email1@example.com", user_id=user.id)
        address2 = Address(email_address="email2@example.com", user_id=user.id)

        db.session.add(address1)
        db.session.add(address2)
        db.session.commit()

        # Combine user and addresses
        # while user is an object of address, it is automatically
        # excluded in addresses due to level_limits to prevent runaway
        # recursion. Because it starts with _eval_value_model, the assumption
        # is that it stems from another model to start.
        value = user
        level_limits = set()
        self.assertTupleEqual(
            (
                {
                    "id": user.id,
                    "name": "Bob",
                    "addresses": [
                        {
                            "id": 1,
                            "emailAddress": "email1@example.com",
                            "userId": user.id,
                        },
                        {
                            "id": 2,
                            "emailAddress": "email2@example.com",
                            "userId": user.id,
                        },
                    ],
                },
                set([user._class()]),
            ),
            _eval_value_model(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )

        # should find and include the user data as well
        value = address1
        level_limits = set()
        self.assertTupleEqual(
            (
                {
                    "id": 1,
                    "emailAddress": "email1@example.com",
                    "userId": user.id,
                    "user": {"id": user.id, "name": "Bob"},
                },
                set([address1._class(), user._class()]),
            ),
            _eval_value_model(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )
        # test modifications via serial stop lists
        # do it wrong first
        Address.SERIAL_STOPLIST = "user_id"
        self.assertRaises(ValueError, address1._get_serial_stop_list)

        # now remove user_id from via the stop list
        Address.SERIAL_STOPLIST = ["user_id"]
        self.assertSetEqual(
            set(["id", "email_address", "user"]),
            set(address1.get_serial_field_list()),
        )

        # now add email_address to the include list
        # do it wrong first
        Address.SERIAL_LIST = "email_address"
        self.assertRaises(ValueError, address1.get_serial_field_list)

        # now add email_address to the include list
        Address.SERIAL_LIST = ["email_address"]
        self.assertSetEqual(
            set(["email_address"]), set(address1.get_serial_field_list())
        )

        # prove it works with _eval_value_model
        value = address1
        level_limits = set()
        self.assertTupleEqual(
            (
                {"emailAddress": "email1@example.com"},
                set([address1._class()]),
            ),
            _eval_value_model(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )

        # Combine user and addresses
        # still uses SERIAL_LIST from above for addresses
        value = user
        level_limits = set()
        self.assertTupleEqual(
            (
                {
                    "id": user.id,
                    "name": "Bob",
                    "addresses": [
                        {"emailAddress": "email1@example.com"},
                        {"emailAddress": "email2@example.com"},
                    ],
                },
                # set([user._class(), address1._class()])
                # NOTE: not quite sure if address should be included here
                #       it certainly processed an address enough to get the
                #       address.
                set([user._class()]),
            ),
            _eval_value_model(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )

        # Combine user and addresses
        # release SERIAL_LIST restrictions
        # SERIAL_STOPLIST
        Address.SERIAL_LIST = None
        Address.SERIAL_STOPLIST = []

        value = user
        level_limits = set()
        self.assertTupleEqual(
            (
                {
                    "id": user.id,
                    "name": "Bob",
                    "addresses": [
                        {
                            "id": 1,
                            "emailAddress": "email1@example.com",
                            "userId": user.id,
                        },
                        {
                            "id": 2,
                            "emailAddress": "email2@example.com",
                            "userId": user.id,
                        },
                    ],
                },
                # same note as above
                # NOTE: not quite sure if address should be included here
                #       it certainly processed an address enough to get the
                #       address.
                set([user._class()]),
            ),
            _eval_value_model(
                value,
                to_camel_case=True,
                level_limits=level_limits,
                source_class=None,
            ),
        )

    def test_eval_value_model_self_referential(self):
        """Test test_eval_value_model_self_referential

        model values that are self-referential such as network descriptions.

                    node 1
                    |    |
                node 2   node 5
                |    |        |
            node 3   node 4   node 6

        This style is designed to keep loading nodes until the whole
        structure is pulled.

        """
        _eval_value_model = self.dbbase.serializers._eval_value_model

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
        node4 = Node(id=4, data="this is node4")
        node5 = Node(id=5, data="this is node5")
        node6 = Node(id=6, data="this is node6")

        db.session.add(node1)
        db.session.commit()
        node1.children.append(node2)
        db.session.commit()
        node2.children.append(node3)
        db.session.commit()
        node2.children.append(node4)
        db.session.commit()
        node1.children.append(node5)
        db.session.commit()
        node5.children.append(node6)
        db.session.commit()

        value = node1
        self.assertTupleEqual(
            (
                {
                    "children": [
                        {
                            "children": [
                                {
                                    "children": [],
                                    "id": 3,
                                    "data": "this is node3",
                                    "parentId": 2,
                                },
                                {
                                    "children": [],
                                    "id": 4,
                                    "data": "this is node4",
                                    "parentId": 2,
                                },
                            ],
                            "id": 2,
                            "data": "this is node2",
                            "parentId": 1,
                        },
                        {
                            "children": [
                                {
                                    "children": [],
                                    "id": 6,
                                    "data": "this is node6",
                                    "parentId": 5,
                                }
                            ],
                            "id": 5,
                            "data": "this is node5",
                            "parentId": 1,
                        },
                    ],
                    "id": 1,
                    "data": "this is node1",
                    "parentId": None,
                },
                set([node1._class()]),
            ),
            _eval_value_model(
                value,
                to_camel_case=True,
                level_limits=set(),
                source_class=None,
            ),
        )

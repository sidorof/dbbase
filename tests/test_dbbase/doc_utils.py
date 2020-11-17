# tests/test_dbbase/utils.py
"""This module tests doc utility functions."""
from . import DBBaseTestCase
from datetime import date, datetime
import uuid
import sqlalchemy.types as types

from sqlalchemy.dialects.postgresql import UUID, ARRAY


class TestDocUtilities(DBBaseTestCase):
    """Test doc utilities."""

    def setUp(self):
        DBBaseTestCase.setUp(self)
        db = self.db

        def is_postgres():
            return str(self.db.session.bind).find("postgres") > -1

        self.is_postgres = is_postgres()

        status_codes = [
            [0, "New"],
            [1, "Active"],
            [2, "Suspended"],
            [3, "Inactive"],
        ]

        class StatusCodes(types.TypeDecorator):
            """
            Status codes are entered as strings and converted to
            integers when saved to the database.
            """

            impl = types.Integer

            def __init__(self, status_codes, **kw):
                self.choices = dict(status_codes)
                super(StatusCodes, self).__init__(**kw)

            def process_bind_param(self, value, dialect):
                """called when saving to the database"""
                return [k for k, v in self.choices.items() if v == value][0]

            def process_result_value(self, value, dialect):
                """called when pulling from database"""
                return self.choices[value]

        class BigTable(db.Model):
            """Test class with a variety of column types"""

            __tablename__ = "main"

            id = db.Column(
                db.Integer,
                primary_key=True,
                nullable=True,
                comment="Primary key with a value assigned by the database",
                info={"extra": "info here"},
            )

            @property
            def i_am_property(self):
                return "I am a property"

            @property
            def annotated_property(self) -> str:
                return "I am an annotated property"

            def a_function(self) -> str:

                return "a function that will be included in docs"

            def a_function_filtered(self, param1, param2) -> str:
                """excluded due to having multiple parameters"""
                return "a function that will be excluded from docs"

            status_id = db.Column(
                StatusCodes(status_codes),
                nullable=False,
                comment="Choices from a list. String descriptors "
                "change to integer upon saving. Enums without the headache.",
            )

            @db.orm.validates("status_id")
            def _validate_id(self, key, id):
                """_validate_id

                Args:
                    id: (int) : id must be in cls.choices
                """
                if id not in dict(status_codes):
                    raise ValueError("{} is not valid".format(id))
                return id

            # nullable / not nullable
            name1 = db.Column(
                db.String(50), nullable=False, comment="This field is required"
            )
            name2 = db.Column(
                db.String(50),
                nullable=True,
                comment="This field is not required",
            )

            # text default
            name3 = db.Column(
                db.Text,
                default="test",
                nullable=False,
                comment="This field has a default value",
                index=True,
            )

            item_length = db.Column(
                db.Float, nullable=False, comment="This field is a float value"
            )

            item_amount = db.Column(db.Numeric(17, 6), default=0.0)

            # integer and default
            some_small_int = db.Column(
                db.SmallInteger,
                default=0,
                nullable=False,
                comment="This field is a small integer",
            )
            some_int = db.Column(
                db.Integer,
                default=0,
                nullable=False,
                comment="This field is a 32 bit integer",
            )
            some_big_int = db.Column(
                db.BigInteger,
                default=0,
                nullable=False,
                comment="This field is a big integer",
            )

            fk_id = db.Column(
                db.Integer,
                db.ForeignKey("other_table.id"),
                nullable=False,
                comment="This field is constrained by a foreign key on"
                "another table",
            )

            today = db.Column(
                db.Date,
                doc="this is a test",
                info={"test": "this is"},
                comment="This field defaults to today, created at model level",
                default=date.today,
            )

            created_at1 = db.Column(
                db.DateTime,
                default=datetime.now,
                comment="This field defaults to now, created at model level",
            )
            created_at2 = db.Column(
                db.DateTime,
                server_default=db.func.now(),
                comment="This field defaults to now, created at the server"
                "level",
            )
            update_time1 = db.Column(
                db.DateTime,
                onupdate=datetime.now,
                comment="This field defaults only on updates",
            )
            update_time2 = db.Column(
                db.DateTime,
                server_onupdate=db.func.now(),
                comment="This field defaults only on updates, but on the"
                "server",
            )

            unique_col = db.Column(
                db.String(20),
                unique=True,
                comment="This must be a unique value in the database.",
            )

            # adapted from sqlalchemy docs
            abc = db.Column(
                db.String(20),
                server_default="abc",
                comment="This field defaults to text but on the server.",
            )
            index_value = db.Column(
                db.Integer,
                server_default=db.text("0"),
                comment="This field defaults to an integer on the server.",
            )

            __table_args = (
                db.Index("ix_name1_name2", "name1", "name2", unique=True),
            )

        class OtherTable(db.Model):
            __tablename__ = "other_table"
            id = db.Column(db.Integer, primary_key=True, nullable=True)

        self.PostgresTable = None
        if is_postgres():

            class PostgresTable(db.Model):
                __tablename__ = "sample_table"
                id = db.Column(
                    UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
                )

                # array for Postgres only
                example_array1 = db.Column(
                    ARRAY(db.Integer),
                    comment="This is the default array of integers.",
                )
                example_array2 = db.Column(
                    ARRAY(db.Integer, dimensions=2),
                    comment="this is an array of integers with two "
                    "dimensions.",
                )

            self.PostgresTable = PostgresTable

        # for test of recursion issue
        class Node(db.Model):
            __tablename__ = "node"
            id = db.Column(db.Integer, primary_key=True)
            parent_id = db.Column(db.Integer, db.ForeignKey("node.id"))
            children = db.relationship(
                "Node", lazy="joined", order_by="Node.id", join_depth=1
            )

        self.BigTable = BigTable
        self.OtherTable = OtherTable
        self.Node = Node
        self.db.create_all()

    def test_doc_util_types(self):
        """ Test the conversion of generic fields in BigTable.

        """
        db = self.db
        doc_utils = self.dbbase.doc_utils

        tmp = db.inspect(self.BigTable).all_orm_descriptors

        field = "id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "integer", "format": "int32"},
        )

        field = "status_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {
                "type": "integer",
                "format": "int32",
                "choices": {
                    0: "New",
                    1: "Active",
                    2: "Suspended",
                    3: "Inactive",
                },
            },
        )

        field = "name1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "string", "maxLength": 50},
        )

        field = "name2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "string", "maxLength": 50},
        )

        field = "name3"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "text"}
        )

        field = "item_length"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "float"},
        )

        field = "item_amount"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "numeric(17, 6)"},
        )

        field = "some_small_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "integer", "format": "int8"},
        )

        field = "some_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "integer", "format": "int32"},
        )

        field = "some_big_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "integer", "format": "int64"},
        )

        field = "fk_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "integer", "format": "int32"},
        )

        field = "today"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "date"}
        )

        field = "created_at1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "date-time"}
        )

        field = "created_at2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "date-time"},
        )

        field = "update_time1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "date-time"},
        )

        field = "update_time2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type), {"type": "date-time"},
        )

        field = "unique_col"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "string", "maxLength": 20},
        )

        field = "abc"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "string", "maxLength": 20},
        )

        field = "index_value"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._type(expression.type),
            {"type": "integer", "format": "int32"},
        )

        # defaults
        field = "id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "status_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "name1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "name2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "name3"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": "test"}},
        )

        field = "item_length"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "item_amount"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": 0.0}},
        )

        field = "some_small_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": 0}},
        )

        field = "some_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": 0}},
        )

        field = "some_big_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": 0}},
        )

        field = "fk_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "today"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": "date.today"}},
        )

        field = "created_at1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default),
            {"default": {"for_update": False, "arg": "datetime.now"}},
        )

        field = "created_at2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "update_time1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "update_time2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "unique_col"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "abc"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        field = "index_value"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._default(expression.default), {"default": None},
        )

        # onupdate
        field = "update_time1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._onupdate(expression.onupdate),
            {"onupdate": {"for_update": True, "arg": "datetime.now"}},
        )

        # server_default - function
        field = "created_at2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._server_default(expression.server_default),
            {
                "server_default": {
                    "for_update": False,
                    "arg": "db.func.now()",
                    "reflected": False,
                }
            },
        )

        # server_default - value -- text in this case
        field = "abc"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._server_default(expression.server_default),
            {
                "server_default": {
                    "for_update": False,
                    "arg": "abc",
                    "reflected": False,
                }
            },
        )

        # server_default - value -- text in this case
        field = "index_value"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._server_default(expression.server_default),
            {
                "server_default": {
                    "for_update": False,
                    "arg": 'db.text("0")',
                    "reflected": False,
                }
            },
        )

        # server_onupdate
        field = "update_time2"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._server_onupdate(expression.server_onupdate),
            {
                "server_onupdate": {
                    "for_update": True,
                    "arg": "db.func.now()",
                    "reflected": False,
                }
            },
        )

        # example of no server default/onupdate
        field = "created_at1"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._server_default(expression.server_default),
            {"default": None},
        )

        self.assertDictEqual(
            doc_utils._server_onupdate(expression.server_onupdate),
            {"default": None},
        )

        # foreign key
        field = "id"
        expression = tmp[field].expression
        self.assertIsNone(doc_utils._foreign_keys(expression.foreign_keys))

        field = "fk_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils._foreign_keys(expression.foreign_keys),
            {"foreign_key": "other_table.id"},
        )

        field = "today"
        expression = tmp[field].expression
        self.assertIsNone(doc_utils._foreign_keys(expression.foreign_keys))

        # unique and other only_if_true
        field = "id"
        expression = tmp[field].expression
        self.assertTupleEqual(
            doc_utils._only_if_true(expression.unique), (None, None),
        )
        self.assertTupleEqual(
            doc_utils._only_if_true(expression.primary_key), (None, True),
        )

        field = "unique_col"
        expression = tmp[field].expression
        self.assertTupleEqual(
            doc_utils._only_if_true(expression.unique), (None, True),
        )

        # pass throughs -- easist to test by passing through everything
        # name, index, doc, comment, info
        field = "id"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils.process_expression(expression),
            {
                "type": "integer",
                "format": "int32",
                "primary_key": True,
                "nullable": True,
                "comment": "Primary key with a value assigned by the database",
                "info": {"extra": "info here"},
            },
        )

        field = "name3"
        expression = tmp[field].expression
        self.assertDictEqual(
            doc_utils.process_expression(expression),
            {
                "type": "text",
                "nullable": False,
                "default": {"for_update": False, "arg": "test"},
                "comment": "This field has a default value",
                "info": {},
                "index": True,
            },
        )

    def test_doc_postgres(self):

        db = self.db

        if self.PostgresTable is not None:
            self.assertDictEqual(
                db.doc_table(self.PostgresTable),
                {
                    "PostgresTable": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "uuid",
                                "primary_key": True,
                                "nullable": False,
                                "default": {
                                    "for_update": False,
                                    "arg": "uuid4",
                                },
                                "info": {},
                            },
                            "example_array1": {
                                "type": "array",
                                "zero-indexes": False,
                                "items": {
                                    "type": "integer",
                                    "format": "int32",
                                },
                                "nullable": True,
                                "comment": "This is the default array "
                                "of integers.",
                                "info": {},
                            },
                            "example_array2": {
                                "type": "array",
                                "zero-indexes": False,
                                "items": {
                                    "type": "integer",
                                    "format": "int32",
                                },
                                "nullable": True,
                                "comment": "this is an array of integers "
                                "with two dimensions.",
                                "info": {},
                            },
                        },
                        "xml": "PostgresTable",
                    }
                },
            )

    def test_serial_fields_param(self):
        """ test_serial_fields_param

        This test evaluates selecting specific columns.
        A successful test has keys only for those specific
        fields.
        """
        serial_fields = ["id", "name1", "name2", "name3"]

        doc = self.db.doc_table(self.BigTable, serial_fields=serial_fields)

        properties = doc[self.BigTable.__name__]["properties"]

        self.assertListEqual(list(properties.keys()), serial_fields)

    def test_camel_case(self):
        """ test_camel_case

        This test evaluates whether the table column names
        can be converted properly to camel case.
        """
        doc = self.db.doc_table(self.BigTable)
        xlate = self.dbbase.utils.xlate

        snake_case_cols = list(
            doc[self.BigTable.__name__]["properties"].keys()
        )
        camel_case_cols = [xlate(col) for col in snake_case_cols]

        test_doc = self.db.doc_table(self.BigTable, to_camel_case=True)

        test_cols = list(test_doc[self.BigTable.__name__]["properties"].keys())

        self.assertListEqual(camel_case_cols, test_cols)

    def test_node_recursion(self):

        self.assertDictEqual(
            {
                "Node": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int32",
                            "primary_key": True,
                            "nullable": False,
                            "info": {},
                        },
                        "parent_id": {
                            "type": "integer",
                            "format": "int32",
                            "nullable": True,
                            "foreign_key": "node.id",
                            "info": {},
                        },
                        "children": {
                            "readOnly": True,
                            "relationship": {
                                "type": "list",
                                "entity": "Node",
                                "fields": {
                                    "id": {
                                        "type": "integer",
                                        "format": "int32",
                                        "primary_key": True,
                                        "nullable": False,
                                        "info": {},
                                    },
                                    "parent_id": {
                                        "type": "integer",
                                        "format": "int32",
                                        "nullable": True,
                                        "foreign_key": "node.id",
                                        "info": {},
                                    },
                                },
                            },
                        },
                    },
                    "xml": "Node",
                }
            },
            self.db.doc_table(self.Node),
        )

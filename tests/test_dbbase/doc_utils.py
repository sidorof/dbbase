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

                return 'a function that will be included in docs'

            def a_function_filtered(self, param1, param2) -> str:
                """excluded due to having multiple parameters"""
                return 'a function that will be excluded from docs'

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

        self.BigTable = BigTable
        self.OtherTable = OtherTable
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
            {"type": "integer", "format": "int32"},
            doc_utils._type(expression.type),
        )

        field = "status_id"
        expression = tmp[field].expression
        self.assertDictEqual(
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
            doc_utils._type(expression.type),
        )

        field = "name1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "string", "maxLength": 50},
            doc_utils._type(expression.type),
        )

        field = "name2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "string", "maxLength": 50},
            doc_utils._type(expression.type),
        )

        field = "name3"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "text"}, doc_utils._type(expression.type)
        )

        field = "item_length"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "float"}, doc_utils._type(expression.type)
        )

        field = "item_amount"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "numeric(17, 6)"}, doc_utils._type(expression.type)
        )

        field = "some_small_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "integer", "format": "int8"},
            doc_utils._type(expression.type),
        )

        field = "some_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "integer", "format": "int32"},
            doc_utils._type(expression.type),
        )

        field = "some_big_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "integer", "format": "int64"},
            doc_utils._type(expression.type),
        )

        field = "fk_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "integer", "format": "int32"},
            doc_utils._type(expression.type),
        )

        field = "today"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "date"}, doc_utils._type(expression.type)
        )

        field = "created_at1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "date-time"}, doc_utils._type(expression.type)
        )

        field = "created_at2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "date-time"}, doc_utils._type(expression.type)
        )

        field = "update_time1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "date-time"}, doc_utils._type(expression.type)
        )

        field = "update_time2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "date-time"}, doc_utils._type(expression.type)
        )

        field = "unique_col"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "string", "maxLength": 20},
            doc_utils._type(expression.type),
        )

        field = "abc"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "string", "maxLength": 20},
            doc_utils._type(expression.type),
        )

        field = "index_value"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"type": "integer", "format": "int32"},
            doc_utils._type(expression.type),
        )

        # defaults
        field = "id"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "status_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "name1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "name2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "name3"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": "test"}},
            doc_utils._default(expression.default),
        )

        field = "item_length"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "item_amount"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": 0.0}},
            doc_utils._default(expression.default),
        )

        field = "some_small_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": 0}},
            doc_utils._default(expression.default),
        )

        field = "some_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": 0}},
            doc_utils._default(expression.default),
        )

        field = "some_big_int"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": 0}},
            doc_utils._default(expression.default),
        )

        field = "fk_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "today"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": "date.today"}},
            doc_utils._default(expression.default),
        )

        field = "created_at1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": {"for_update": False, "arg": "datetime.now"}},
            doc_utils._default(expression.default),
        )

        field = "created_at2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "update_time1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "update_time2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "unique_col"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "abc"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        field = "index_value"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None}, doc_utils._default(expression.default)
        )

        # onupdate
        field = "update_time1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"onupdate": {"for_update": True, "arg": "datetime.now"}},
            doc_utils._onupdate(expression.onupdate),
        )

        # server_default - function
        field = "created_at2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {
                "server_default": {
                    "for_update": False,
                    "arg": "db.func.now()",
                    "reflected": False,
                }
            },
            doc_utils._server_default(expression.server_default),
        )

        # server_default - value -- text in this case
        field = "abc"
        expression = tmp[field].expression
        self.assertDictEqual(
            {
                "server_default": {
                    "for_update": False,
                    "arg": "abc",
                    "reflected": False,
                }
            },
            doc_utils._server_default(expression.server_default),
        )

        # server_default - value -- text in this case
        field = "index_value"
        expression = tmp[field].expression
        self.assertDictEqual(
            {
                "server_default": {
                    "for_update": False,
                    "arg": 'db.text("0")',
                    "reflected": False,
                }
            },
            doc_utils._server_default(expression.server_default),
        )

        # server_onupdate
        field = "update_time2"
        expression = tmp[field].expression
        self.assertDictEqual(
            {
                "server_onupdate": {
                    "for_update": True,
                    "arg": "db.func.now()",
                    "reflected": False,
                }
            },
            doc_utils._server_onupdate(expression.server_onupdate),
        )

        # example of no server default/onupdate
        field = "created_at1"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"default": None},
            doc_utils._server_default(expression.server_default),
        )

        self.assertDictEqual(
            {"default": None},
            doc_utils._server_onupdate(expression.server_onupdate),
        )

        # foreign key
        field = "id"
        expression = tmp[field].expression
        self.assertIsNone(doc_utils._foreign_keys(expression.foreign_keys))

        field = "fk_id"
        expression = tmp[field].expression
        self.assertDictEqual(
            {"foreign_key": "other_table.id"},
            doc_utils._foreign_keys(expression.foreign_keys),
        )

        field = "today"
        expression = tmp[field].expression
        self.assertIsNone(doc_utils._foreign_keys(expression.foreign_keys))

        # unique and other only_if_true
        field = "id"
        expression = tmp[field].expression
        self.assertTupleEqual(
            (None, None), doc_utils._only_if_true(expression.unique)
        )
        self.assertTupleEqual(
            (None, True), doc_utils._only_if_true(expression.primary_key)
        )

        field = "unique_col"
        expression = tmp[field].expression
        self.assertTupleEqual(
            (None, True), doc_utils._only_if_true(expression.unique)
        )

        # pass throughs -- easist to test by passing through everything
        # name, index, doc, comment, info
        field = "id"
        expression = tmp[field].expression
        self.assertDictEqual(
            {
                "type": "integer",
                "format": "int32",
                "primary_key": True,
                "nullable": True,
                "comment": "Primary key with a value assigned by the database",
                "info": {"extra": "info here"},
            },
            doc_utils.process_expression(expression),
        )

        field = "name3"
        expression = tmp[field].expression
        self.assertDictEqual(
            {
                "type": "text",
                "nullable": False,
                "default": {"for_update": False, "arg": "test"},
                "comment": "This field has a default value",
                "info": {},
                "index": True,
            },
            doc_utils.process_expression(expression),
        )

    def test_doc_postgres(self):

        db = self.db

        if self.PostgresTable is not None:

            self.assertDictEqual(
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
                                "comment": "this is an array of integers"
                                "with two dimensions.",
                                "info": {},
                            },
                        },
                        "xml": "PostgresTable"
                    }
                },
                db.doc_table(self.PostgresTable),
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

        self.assertListEqual(serial_fields, list(properties.keys()))

    def test_column_prop_param(self):
        """ test_column_prop_param

        This test evaluates whether specific properties for columns
        can be pulled. A successful test has keys only for those
        properties.

        Depending on the property, a specific column might not have
        it. However, there should not be a prop outside of the list.
        """
        selected_properties = ["default", "nullable"]
        doc = self.db.doc_table(self.BigTable, column_props=selected_properties)

        data = doc[self.BigTable.__name__]["properties"]

        for column_props in data.values():

            for key in column_props.keys():
                with self.subTest(key=key):
                    self.assertIn(key, selected_properties)

    def test_camel_case(self):
        """ test_camel_case

        This test evaluates whether the table column names
        can be converted properly to camel case.
        """
        doc = self.db.doc_table(self.BigTable)
        xlate = self.dbbase.utils.xlate

        snake_case_cols = list(doc[self.BigTable.__name__]["properties"].keys())
        camel_case_cols = [xlate(col) for col in snake_case_cols]

        test_doc = self.db.doc_table(self.BigTable, to_camel_case=True)

        test_cols = list(test_doc[self.BigTable.__name__]["properties"].keys())

        self.assertListEqual(camel_case_cols, test_cols)

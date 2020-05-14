# examples/table_documentation.py
"""
This example mirrors the user guide example for documentation
dictionaries.

This is simply a table with different kinds of columns and parameter choices.
The StatusCodes class is included as a method for illustrating a selection
of choices that would be converted to a status code. There are several ways
to do this, this is one of several.

BigTable is the class is created. The function `db.doc_table` creates the
output.

For clarity, the output converted to JSON format.

`print(json.dumps(db.doc_table(BigTable), indent=4))`

"""
import json
from datetime import date, datetime
import sqlalchemy.types as types

from dbbase import DB

db = DB(config=":memory:")

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

    __tablename__ = "big_table"

    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=True,
        comment="Primary key with a value assigned by the database",
        info={"extra": "info here"},
    )

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
        db.String(50), nullable=True, comment="This field is not required",
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
        comment="This field defaults to now, created at the server" "level",
    )
    update_time1 = db.Column(
        db.DateTime,
        onupdate=datetime.now,
        comment="This field defaults only on updates",
    )
    update_time2 = db.Column(
        db.DateTime,
        server_onupdate=db.func.now(),
        comment="This field defaults only on updates, but on the" "server",
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

    __table_args = (db.Index("ix_name1_name2", "name1", "name2", unique=True),)


class OtherTable(db.Model):
    """
    This table is used solely to enable an option for a foreign key.
    """

    __tablename__ = "other_table"
    id = db.Column(db.Integer, primary_key=True, nullable=True)


# using JSON for a better output

print(json.dumps(db.doc_table(BigTable), indent=4))

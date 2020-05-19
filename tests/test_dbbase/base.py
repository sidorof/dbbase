# test/test_dbbase/base.py
from . import DBBaseTestCase


class TestDBBaseClass(DBBaseTestCase):
    """
    This class tests DB class functions

    Deferred this due to the test fixture using all of these
    anyway.
    """

    def test__DB__init__(self):
        """ test__DB__init__

        """
        DB = self.dbbase.DB

        # test defaults
        # must have config
        self.assertRaises(TypeError, DB)

        db = DB(self.config)
        self.assertIsInstance(db, DB)

        self.assertEqual(db.config, self.config)

        # NOTE: could do testing of essential
        #       attributes of Model

        self.assertEqual(db, db.Model.db)

        # If create_session moved out no need to
        #   check for checkfirst, echo here
        # checkfirst True/False goes here

        # echo

        # test self.attributes

    def test_doc_table(self):
        """test_doc_table

        This test ensures that only columns, not relations are passed to
        process_expression.
        """
        db = self.db

        class Table1(db.Model):
            __tablename__ = "table1"
            id = db.Column(db.Integer, primary_key=True)
            table2 = db.relationship(
                "Table2", backref="table1", lazy="immediate"
            )

        class Table2(db.Model):
            __tablename__ = "table2"
            id = db.Column(db.Integer, primary_key=True)

            table1_id = db.Column(db.Integer, db.ForeignKey("table1.id"))

        class Table0(db.Model):
            __tablename__ = "table0"
            id = db.Column(db.Integer, primary_key=True)

            table1_id = db.Column(db.Integer, db.ForeignKey("table1.id"))

        db.create_all()

        # Table1
        self.assertDictEqual(
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
                        "table2": {
                            "readOnly": True,
                            "relationship": {
                                "type": "list",
                                "entity": "Table2"
                            }
                        }
                    },
                    "xml": "Table1",
                }
            },
            db.doc_table(Table1),
        )

        # Table2
        self.assertDictEqual(
            {
                "Table2": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int32",
                            "primary_key": True,
                            "nullable": False,
                            "info": {},
                        },
                        "table1_id": {
                            "type": "integer",
                            "format": "int32",
                            "nullable": True,
                            "foreign_key": "table1.id",
                            "info": {},
                        },
                        "table1": {
                            "readOnly": True,
                            "relationship": {
                                "type": "single",
                                "entity": "Table1"
                            }
                        }
                    },
                    "xml": "Table2",
                }
            },
            db.doc_table(Table2),
        )

        # Test doc_tables
        doc = db.doc_tables()
        self.assertDictEqual(
            {
                "definitions": {
                    "Table0": {
                        "type": "object",
                        "properties": {
                            "table1_id": {
                                "type": "integer",
                                "format": "int32",
                                "nullable": True,
                                "foreign_key": "table1.id",
                                "info": {},
                            },
                            "id": {
                                "type": "integer",
                                "format": "int32",
                                "primary_key": True,
                                "nullable": False,
                                "info": {},
                            },
                        },
                        "xml": "Table0",
                    },
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
                            "table2": {
                                "readOnly": True,
                                "relationship": {
                                    "type": "list",
                                    "entity": "Table2"
                                }
                            }
                        },
                        "xml": "Table1",
                    },
                    "Table2": {
                        "type": "object",
                        "properties": {
                            "table1_id": {
                                "type": "integer",
                                "format": "int32",
                                "nullable": True,
                                "foreign_key": "table1.id",
                                "info": {},
                            },
                            "id": {
                                "type": "integer",
                                "format": "int32",
                                "primary_key": True,
                                "nullable": False,
                                "info": {},
                            },
                            "table1": {
                                "readOnly": True,
                                "relationship": {
                                    "type": "single",
                                    "entity": "Table1"
                                }
                            }
                        },
                        "xml": "Table2",
                    },
                }
            },
            doc,
        )

        # correct number
        self.assertEqual(3, len(doc["definitions"].keys()))

        # does it sort
        self.assertListEqual(
            ["Table0", "Table1", "Table2"],
            [key for key in doc["definitions"].keys()],
        )

        # does class list work
        doc = db.doc_tables(class_list=[Table2])
        self.assertEqual(1, len(list(doc["definitions"].keys())))
        self.assertEqual("Table2", list(doc["definitions"].keys())[0])

        # does it pass through camel flag
        doc = db.doc_tables(class_list=[Table2], to_camel_case=True)
        self.assertIn(
            "table1Id", list(doc["definitions"]["Table2"]["properties"].keys())
        )

        # does it pass through column props filter
        doc = db.doc_tables(column_props=["nullable", "primary_key"])

        self.assertNotIn(
            "type", list(doc["definitions"]["Table2"]["properties"].keys())
        )

        # test doc_column - no need to create new tables for this.
        self.assertDictEqual(
            {
                'type': 'integer',
                'format': 'int32',
                'nullable': True,
                'foreign_key': 'table1.id',
                'info': {}
            },
            db.doc_column(Table2, 'table1_id')
        )

    def test__process_table_args(self):
        """test__process_table_args

        Does it process constraints in Table Args for docs

        Test
            Unique
            ForeignKeys
            CheckConstraints

        """
        db = self.db

        class NewModel(db.Model):

            __tablename__ = 'new_model'
            id = db.Column(db.Integer, primary_key=True)
            uniq_fld = db.Column(db.String)
            value = db.Column(db.Integer)
            __table_args__ = (
                db.ForeignKeyConstraint(['id'], ['related.id']),
                db.UniqueConstraint('uniq_fld'),
                db.CheckConstraint('value > 10', name='chk_value')
            )

        class RelatedModel(db.Model):

            __tablename__ = 'related'
            id = db.Column(db.Integer, primary_key=True)

        db.create_all()

        self.assertDictEqual(
            {
                "constraints": [
                    {
                        "foreign_key_constraint": {
                            "foreign_key": "related.id",
                            "column_keys": [
                                "id"
                            ]
                        }
                    },
                    {
                        "unique_contraint": {
                            "columns": [
                                "uniq_fld"
                            ]
                        }
                    },
                    {
                        "check_constraint": "value > 10"
                    }
                ]
            },
            db._process_table_args(NewModel)
        )

    def test_create_engine(self):
        pass
        # test defaults

        # test self.attributes

        # test return

    def test_create_session(self):
        pass
        # test defaults

        # test self.attributes

        # test return

    def test_drop_all(self):
        pass
        # test defaults

        # test self.attributes

        # test return

    def test_reload_model(self):
        pass
        # test defaults

        # test self.attributes

        # test return

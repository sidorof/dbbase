# tests/__init__.py

import unittest

from . test_dbbase.test_db_utils import TestUtilities
from . test_dbbase.test_dbinfo import TestDBInfo
#from . test_dbbase.test_model import TestModelClass



#suite = TestSuite()

#suite.addTest(TestUtilities())

configs = [
    {
        "testdb_uri": ":memory:",
        "testdb_vars": {}
    },
    {
        "testdb_uri": "sqlite:///{dbname}.db",
        "testdb_vars": {"dbname": "testdb"}
    },
    {
        "testdb_uri": 'postgresql://{user}@{host}:{port}/{basedb}',
        "testdb_vars": {
            "dbname": "testdb",
            "user": "suser",
            "host": "localhost",
            "port": "5432",
            "base_db": "postgres"
        }
    }
]


for config in configs:
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    # set database variables for the type of database to be tested
    TestDBInfo.TESTDB_URI = config["testdb_uri"]
    TestDBInfo.TESTDB_VARS = config["testdb_vars"]
    suite.addTests(loader.loadTestsFromModule(TestDBInfo()))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
    print('result', result)

# tests/__init__.py
"""
This module runs the tests for dbbase. To account for multiple
configurations a list of configs is loaded from the parent directory with
some standard names. That file should be altered to accommodate the
expected usage on your systems.

For each configuration, the set of test cases are run to ensure that
everything works as expected.
"""
import json
import unittest

from . test_dbbase.db_utils import TestUtilities
from . test_dbbase.dbinfo import TestDBInfoClass
from . test_dbbase.model import TestModelClass

CONFIG_FILE = 'sample_configs.json'
with open(CONFIG_FILE) as fobj:
    configs = json.loads(fobj.read())

test_cases = [
    TestDBInfoClass,
    TestModelClass
]

for config in configs:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestUtilities))

    # set database variables for the type of database to be tested
    for test_case in test_cases:
        test_case.TESTDB_URI = config["testdb_uri"]
        test_case.TESTDB_VARS = config["testdb_vars"]

    print('config', config)
    suite.addTests(loader.loadTestsFromTestCase(TestDBInfoClass))
    suite.addTests(loader.loadTestsFromTestCase(TestModelClass))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)

    print('result', result)

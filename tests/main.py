# tests/__init__.py
"""
This module runs the tests for dbbase. To account for multiple
configurations a list of configs is loaded from the parent directory with
some standard names. That file should be altered to accommodate the
expected usage on your systems.

For each configuration, the set of test cases are run to ensure that
everything works as expected.
"""
import os
import json
import unittest

from .test_dbbase.utils import TestUtilities
from .test_dbbase.base import TestDBBaseClass
from .test_dbbase.model import TestModelClass
from .test_dbbase.serializers import TestSerializers

# list of sample configs to test
SAMPLE_CONFIGS = "sample_configs.json"

# temporary created for the current test, deleted after
CONFIG_FILE = "config.json"


with open(SAMPLE_CONFIGS) as fobj:
    configs = json.loads(fobj.read())

for config in configs:
    print("testing config: {}".format(config["name"]))
    with open(CONFIG_FILE, "w") as fobj:
        json.dump(config, fobj)
    suite = unittest.TestSuite()

    suite.addTests(unittest.makeSuite(TestSerializers))
    suite.addTests(unittest.makeSuite(TestUtilities))
    suite.addTests(unittest.makeSuite(TestModelClass))
    suite.addTests(unittest.makeSuite(TestDBBaseClass))

    test_result = unittest.TextTestRunner()
    test_result = unittest.TextTestRunner(failfast=True, verbosity=1).run(
        suite
    )

    print("result", test_result)
    print()
    for line in test_result.errors:
        print("location: {}".format(line[0]))
        print("traceback: {}".format(line[1]))

    for line in test_result.failures:
        print("location: {}".format(line[0]))
        print("traceback: {}".format(line[1]))

    print()
    print("success", test_result.wasSuccessful())

    print("completed testing with config: {}".format(config["name"]))
    os.remove(CONFIG_FILE)

print("completed all testing")

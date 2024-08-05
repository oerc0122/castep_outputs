# pylint: skip-file
import unittest
import doctest
from castep_outputs.utilities import utility, castep_res

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utility))
    tests.addTests(doctest.DocTestSuite(castep_res))
    return tests

#!/usr/bin/env python3

# Scaffolding necessary to set up ACCESS test
import sys
try: from universal.harness import *
except: sys.path.append("../../universal/"); from harness import *

# Grading test suite starts here

import inspect
import json
import script as implementation

class PublicTestSuite(AccessTestSuite):

    @feedback(1, "x is not 42")
    def test_x_is_42(self):
        self.assertEqual(implementation.x, 42)

    @feedback(1, "The solution seems to contain x = 42, please assign something slighty more complex")
    def test_x_is_not_literally_42(self):
        self.test_x_is_42()
        source = inspect.getsource(implementation)
        self.assertTrue("x=42" not in ''.join(source.split()))


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

    # Invalid: test not giving expected full points (1 instead of 2)


#!/usr/bin/env python3

# Scaffolding necessary to set up ACCESS test
import sys
try: from universal.harness import *
except: sys.path.append("../../universal/"); from harness import *

# Grading test suite starts here

script = grading_import("task", "script")

class GradingTests(AccessTestCase):

    def _test(self, sentence, expected):
        actual = script.reverse_words(sentence)
        self.hint(f"Reversal not correct for sentence='{sentence}'... expected result is '{expected}'!")
        self.assertEqual(expected, actual)

    def test_case1(self):
        self._test("Hello World", "World Hello")

    def test_case2(self):
        self._test("  This   is  a  test  ", "test a is This")

    def test_case3(self):
        self._test("Python", "Python")

    def test_case4(self):
        self._test("", "")

    def test_case5(self):
        self._test("Hello, World!", "World! Hello,")

    def test_case6(self):
        self._test("123 456 789", "789 456 123")

TestRunner().run(AccessTestSuite(1, [GradingTests]))

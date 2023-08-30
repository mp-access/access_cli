#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class CommandExecutionTests(unittest.TestCase):

    def validator(self, directory, commands, global_file=[], course_root=None):
        from access_cli_sealuzh.main import AccessValidator
        print(directory)
        print(str(directory))
        args = SimpleNamespace(directory=str(directory), execute=True, verbose=False,
                               global_file=global_file, course_root=course_root,
                               run=0 if "run" in commands else None,
                               test=0 if "test" in commands else None,
                               grade_template=True if "template" in commands else False,
                               grade_solution=True if "solution" in commands else False,
                               solve_command = "cp solution.py script.py",
                               level="task", recursive=False,)
        return AccessValidator(args)

    def test_valid_config(self):
        validator = self.validator(files('tests.resources.execute').joinpath('valid'),
          ["run", "test", "template", "solution"])
        valid, errors = validator.run()
        self.assertEqual(0, len(errors))

    def test_global_file(self):
        validator = self.validator(files('tests.resources.execute.global-file.as').joinpath('task'),
          ["template"], global_file=["universal/harness.py"],
          course_root=str(files('tests.resources.execute').joinpath('global-file')))
        valid, errors = validator.run()
        self.assertEqual(0, len(errors))

    def test_invalid_run_command(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('run-command-returns-nonzero'),
            ["run"])
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("Expected returncode 0 but got ", errors[0])

    def test_invalid_test_command(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('test-command-returns-nonzero'),
            ["test"])
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("Expected returncode 0 but got ", errors[0])

    def test_grading_gives_points_for_template(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('grading-gives-points-for-template'),
            ["template"])
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("1 points awarded instead of expected 0", errors[0])

    def test_grading_not_giving_max_points_for_solution(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('grading-not-giving-max-points-for-solution'),
            ["solution"])
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("1 points awarded instead of expected 2", errors[0])


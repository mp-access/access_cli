#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class CommandExecutionTests(unittest.TestCase):

    def validator(self, directory, commands, global_file=None, course_root=None):
        if global_file is None: global_file=set()
        from access_cli_sealuzh.main import AccessValidator
        args = SimpleNamespace(directory=str(directory), execute=True, verbose=False,
                               global_file=global_file, course_root=course_root,
                               run=0 if "run" in commands else None, user="",
                               test=1 if "test" in commands else None,
                               test_solution=True if "test_solution" in commands else False,
                               grade_template=True if "template" in commands else False,
                               grade_solution=True if "solution" in commands else False,
                               solve_command = "cp solution.py script.py",
                               level="task", recursive=False)
        return AccessValidator(args)

    def test_valid_config(self):
        validator = self.validator(files('tests.resources.execute').joinpath('valid'),
          ["run", "test", "test_solution", "template", "solution"])
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_valid_config_without_test_command(self):
        validator = self.validator(files('tests.resources.execute').joinpath('valid-no-test'),
          ["run", "test", "test_solution", "template", "solution"])
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_global_file(self):
        validator = self.validator(files('tests.resources.execute.global-file.as').joinpath('task'),
          ["template"], global_file=["universal/harness.py"],
          course_root=str(files('tests.resources.execute').joinpath('global-file')))
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_invalid_run_command(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('run-command-returns-nonzero'),
            ["run"])
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("Expected returncode 0 but got ", errors[0])

    def test_test_template_succeeds(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('test-on-template-returns-zero'),
            ["test"])
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("Expected returncode 1 but got ", errors[0])

    def test_test_on_solution_fails(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('test-on-solution-returns-nonzero'),
            ["test_solution"])
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("Expected returncode 0 but got ", errors[0])

    def test_grading_gives_points_for_template(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('grading-gives-points-for-template'),
            ["template"])
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("1 points awarded instead of expected 0", errors[0])

    def test_grading_not_giving_max_points_for_solution(self):
        validator = self.validator(
            files('tests.resources.execute').joinpath('grading-not-giving-max-points-for-solution'),
            ["solution"])
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("1 points awarded instead of expected 2", errors[0])


#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class RecursiveValidationTests(unittest.TestCase):

    def validator(self, directory):
        from access_cli_sealuzh.main import AccessValidator
        args = SimpleNamespace(directory=str(directory), execute=False,
                               global_file=set(), user="", test_solution=False,
                               run=None, test=None, verbose=False,
                               grade_template=False, grade_solution=False,
                               level="course", recursive=True)
        return AccessValidator(args)

    def test_valid_config(self):
        validator = self.validator(files('tests.resources.recursive').joinpath('valid'))
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_task_missing_file(self):
        validator = self.validator(files('tests.resources.recursive').joinpath('task-missing-file'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("files references non-existing file", errors[0])


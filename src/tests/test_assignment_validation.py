#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class AssignmentValidationTests(unittest.TestCase):

    def validator(self, directory):
        from access_cli_sealuzh.main import AccessValidator
        args = SimpleNamespace(directory=str(directory), execute=False,
                               global_file=[], user="",
                               run=None, test=None, verbose=False,
                               grade_template=False, grade_solution=False,
                               level="assignment", recursive=False)
        return AccessValidator(args)

    def test_valid_config(self):
        validator = self.validator(files('tests.resources.assignment').joinpath('valid'))
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_invalid_dates(self):
        validator = self.validator(files('tests.resources.assignment').joinpath('invalid-dates'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("start is after end", errors[0])

    def test_invalid_tasks(self):
        validator = self.validator(files('tests.resources.assignment').joinpath('invalid-tasks'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("references non-existing task", errors[0])

    def test_missing_en_information(self):
        validator = self.validator(files('tests.resources.assignment').joinpath('missing-en-information'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("missing information for language 'en'", errors[0])

    def test_missing_information_attributes(self):
        validator = self.validator(files('tests.resources.assignment').joinpath('missing-information-attributes'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("information schema errors", errors[0])


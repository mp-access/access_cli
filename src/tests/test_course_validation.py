#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class CourseValidationTests(unittest.TestCase):

    def validator(self, directory):
        from access_cli_sealuzh.main import AccessValidator
        args = SimpleNamespace(directory=str(directory), execute=False,
                               global_file=set(), user="", test_solution=False,
                               run=None, test=None, verbose=False,
                               grade_template=False, grade_solution=False,
                               level="course", recursive=False)
        return AccessValidator(args)

    def test_valid_config(self):
        validator = self.validator(files('tests.resources.course').joinpath('valid'))
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_valid_minimal_config(self):
        validator = self.validator(files('tests.resources.course').joinpath('valid-minimal'))
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors))

    def test_invalid_assignments(self):
        validator = self.validator(files('tests.resources.course').joinpath('invalid-assignments'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("references non-existing assignment", errors[0])

    def test_invalid_logo(self):
        validator = self.validator(files('tests.resources.course').joinpath('invalid-logo'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("references non-existing logo", errors[0])

    def test_invalid_override_dates(self):
        validator = self.validator(files('tests.resources.course').joinpath('invalid-override-dates'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("override_start is after override_end", errors[0])

    def test_missing_en_information(self):
        validator = self.validator(files('tests.resources.course').joinpath('missing-en-information'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("missing information for language 'en'", errors[0])

    def test_missing_global_file(self):
        validator = self.validator(files('tests.resources.course').joinpath('missing-global-file'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("global files references non-existing file", errors[0])

    def test_missing_information_attributes(self):
        validator = self.validator(files('tests.resources.course').joinpath('missing-information-attributes'))
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))
        self.assertIn("information schema errors", errors[0])


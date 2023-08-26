#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class TaskValidationTests(unittest.TestCase):

    def validator(self, directory):
        from access_cli_sealuzh.main import AccessValidator
        args = SimpleNamespace(directory=str(directory), execute=False,
                               global_file=[],
                               run=None, test=None, verbose=False,
                               grade_template=False, grade_solution=False,
                               level="task", recursive=False)
        return AccessValidator(args)

    def test_valid_config(self):
        validator = self.validator(files('tests.resources.task').joinpath('valid'))
        valid, errors = validator.run()
        self.assertEqual(0, len(errors))

    def test_valid_minimal_config(self):
        validator = self.validator(files('tests.resources.task').joinpath('valid-minimal'))
        valid, errors = validator.run()
        self.assertEqual(0, len(errors))

    def test_grading_should_not_be_editable(self):
        validator = self.validator(files('tests.resources.task').joinpath('grading-should-not-be-editable'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))

    def test_grading_should_not_be_visible(self):
        validator = self.validator(files('tests.resources.task').joinpath('grading-should-not-be-editable'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))

    def test_invisible_should_not_be_editable(self):
        validator = self.validator(files('tests.resources.task').joinpath('grading-should-not-be-editable'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))

    def test_solution_should_not_be_editable(self):
        validator = self.validator(files('tests.resources.task').joinpath('grading-should-not-be-editable'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))

    def test_missing_file(self):
        validator = self.validator(files('tests.resources.task').joinpath('missing-file'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("files references non-existing file", errors[0])

    def test_missing_en_information(self):
        validator = self.validator(files('tests.resources.task').joinpath('missing-en-information'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("missing information for language 'en'", errors[0])

    def test_missing_information_attributes(self):
        validator = self.validator(files('tests.resources.task').joinpath('missing-information-attributes'))
        valid, errors = validator.run()
        self.assertEqual(1, len(errors))
        self.assertIn("information schema errors", errors[0])


#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from importlib.resources import files

class RecursiveValidationTests(unittest.TestCase):

    def validator(self, directory):
        from access_cli_sealuzh.main import AccessValidator, autodetect
        args = SimpleNamespace(directory=str(directory), course_root=None,
                               solve_command="rm -R task; cp -R solution task",
                               grade_template = False, grade_solution=False,
                               global_file=[], verbose=False, recursive=False)
        args = autodetect(args)
        return AccessValidator(args)

    def test_course(self):
        validator = self.validator(files('tests.resources.autodetect').joinpath('valid-course'))
        valid, errors = validator.run()
        self.assertEqual(0, len(errors))

    def test_assignment(self):
        validator = self.validator(files('tests.resources.autodetect.valid-course').joinpath('assignment'))
        valid, errors = validator.run()
        self.assertEqual(0, len(errors))

    def test_task(self):
        validator = self.validator(files('tests.resources.autodetect.valid-course.assignment').joinpath('task'))
        valid, errors = validator.run()
        print(errors)
        self.assertEqual(0, len(errors))


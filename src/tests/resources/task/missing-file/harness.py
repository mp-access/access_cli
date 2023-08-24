import unittest
import inspect
import json
import script as implementation

class AccessTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep track of which test methods succeeded AT LEAST once.
        # We do this because in any actual test, you could
        # call another test method as a prerequisite, see for example
        # /02_basics/variable_assignment/grading/tests.py.
        # To not double-count any test executions, nor double-award
        # points and to avoid flakiness, we consider a test as
        # successful if it succeeded at least once. This is tracked
        # via setUp and tearDown
        cls.results = {}
        # The hints and points for each test method are stored
        # via the feedback decorator specified below
        cls.hints = {}
        cls.points = {}

    @classmethod
    def tearDownClass(cls):
        # Prepare the grading output
        cls.grade_results = {'points': 0, 'hints': []}
        # Figure out the order of tests in the test suite
        test_methods = [name for name, value in cls.__dict__.items()
                        if callable(value) and name.startswith("test")]
        # In test definition order...
        for test in test_methods:
            # ... add hints for failed tests
            if not cls.results[test]:
                cls.grade_results["hints"].append(cls.hints[test])
            # ... add points for successful tests
            else:
                cls.grade_results["points"] += cls.points[test]
        # write results to file read by ACCESS
        with open('grade_results.json', 'w') as grade_results_file:
            json.dump(cls.grade_results, grade_results_file)

    def setUp(self):
        # Snapshot current overall test results so we'll be able
        # to compare with after the test runs
        self._initial_errors = len(self._outcome.result.errors)
        self._initial_failures = len(self._outcome.result.failures)

    def tearDown(self):
        # Figure out if this particular test was a success
        test_name = self._testMethodName
        if len(self._outcome.result.errors) > self._initial_errors or \
           len(self._outcome.result.failures) > self._initial_failures:
            # Only override the result if we don't already have a result
            if test_name not in self.results:
                self.results[test_name] = False
        else:
            # Overriding as a success is always OK
            self.results[test_name] = True

def feedback(points, message):
    """Supply the awarded points and hint for a given test method"""
    def decorator(func):
        test_name = func.__name__
        def wrapper(*args, **kwargs):
            instance = args[0]
            instance.points[test_name] = points
            instance.hints[test_name] = message
            return func(*args, **kwargs)
        return wrapper
    return decorator



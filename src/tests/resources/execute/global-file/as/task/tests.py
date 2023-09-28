from unittest import TestCase

# You don't need to worry about this yet.
class PublicTestSuite(TestCase):

    def test_x_is_42(self):
        import script
        x = script.x
        assertEqual(x, 42)


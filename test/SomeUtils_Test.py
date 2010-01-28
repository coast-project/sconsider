import unittest, SomeUtils

class SomeUtilsTest(unittest.TestCase):
    def testMultipleReplace(self):
        text = "this is a dummy text for testing"
        result = SomeUtils.multiple_replace([
                                             ('dummy', 'fantastic'),
                                             ('text', 'string'),
                                             ('^t\S*', 'blub')
                                            ], text)
        self.assertEqual("blub is a fantastic string for testing", result)

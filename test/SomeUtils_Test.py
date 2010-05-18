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

class AllFuncsTest(unittest.TestCase):
    def setUp(self):
        self.funcs = [lambda *attrs: True, lambda *attrs: True, lambda *attrs: True]
    
    def testAllFuncsTrue(self):        
        self.assertTrue(SomeUtils.allFuncs(self.funcs, "blub"))
        
    def testAllFuncsFalse(self):
        self.funcs.append(lambda *attrs: False)        
        self.assertFalse(SomeUtils.allFuncs(self.funcs, "blub"))
        
    def testAllFuncsMultipleArgs(self):        
        self.assertTrue(SomeUtils.allFuncs(self.funcs, "blub", "bla", "bloek"))
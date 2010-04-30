import unittest
from Anything import *

class AnythingTest(unittest.TestCase):
	def setUp(self):
		self.any1 = Anything()
		self.any1['a'] = 1
		self.any1['b'] = 2
		self.any1.append(3)
		self.any1['c'] = 4
		self.any1.append(5)
	
	def testLen(self):
		self.assertEqual(5, len(self.any1))
	
	def testContent(self):
		self.assertEqual(1, self.any1['a'])
		self.assertEqual(2, self.any1['b'])
		self.assertEqual(4, self.any1['c'])
		self.assertEqual(1, self.any1[0])
		self.assertEqual(2, self.any1[1])
		self.assertEqual(3, self.any1[2])
		self.assertEqual(4, self.any1[3])
		self.assertEqual(5, self.any1[4])
	
	def testSetWithPos(self):
		self.any1[0] = 99
		self.assertEqual(99, self.any1['a'])
		
	def testSetWithKey(self):
		self.any1['a'] = 99
		self.assertEqual(99, self.any1[0])
	
	def testArrayIteration(self):
		i = 1
		for v in self.any1:
			self.assertEqual(i, v)
			i += 1
			
	def testItems(self):
		expected = {
			'a': 1,
			'b': 2,
			'c': 4
		}
		self.assertEqual(expected, dict(self.any1.items()))
		
	def testIteritems(self):
		expected = {
			'a': 1,
			'b': 2,
			'c': 4
		}
		self.assertEqual(expected, dict(self.any1.iteritems()))
		
	def testKeys(self):
		self.assertEqual(sorted(['a', 'b', 'c']), sorted(self.any1.keys()))
	
	def testIterkeys(self):
		self.assertEqual(sorted(['a', 'b', 'c']), sorted(self.any1.iterkeys()))
	
	def testSlotname(self):
		self.assertEqual('a', self.any1.slotname(0))
		self.assertEqual('b', self.any1.slotname(1))
		self.assertEqual('c', self.any1.slotname(3))
		self.assertEqual(None, self.any1.slotname(2))
		self.assertEqual(None, self.any1.slotname(5))

	def testStr(self):
		expected = str([1, 2, 3, 4, 5])
		self.assertEqual(expected, str(self.any1))
		
	def testHasKey(self):
		self.assertTrue(self.any1.has_key('a'))
		self.assertTrue(self.any1.has_key('b'))
		self.assertTrue(self.any1.has_key('c'))
		self.assertFalse(self.any1.has_key('d'))
		
	def testContains(self):
		for i in xrange(1, 5):
			self.assertTrue(i in self.any1)
		self.assertFalse(0 in self.any1)
		self.assertTrue(6 not in self.any1)
	

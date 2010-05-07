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
        expected = map(lambda i: i+1, range(5))
        self.assertEqual(expected, [v for v in self.any1])

    def testItervalues(self):
        expected = [1, 2, 4]
        self.assertEqual(sorted(expected), sorted(list(self.any1.itervalues())))
    
    def testItervaluesAll(self):
        expected = map(lambda i: i+1, range(5))
        self.assertEqual(expected, list(self.any1.itervalues(all=True)))

    def testValues(self):
        expected = [1, 2, 4]
        self.assertEqual(sorted(expected), sorted(list(self.any1.values())))
    
    def testValuesAll(self):
        expected = map(lambda i: i+1, range(5))
        self.assertEqual(expected, list(self.any1.values(all=True)))
            
    def testItems(self):
        expected = {
            'a': 1,
            'b': 2,
            'c': 4
        }
        self.assertEqual(expected, dict(self.any1.items()))
        
    def testItemsAll(self):
        expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
        self.assertEqual(expected, self.any1.items(all=True))
        
    def testIteritems(self):
        expected = {
            'a': 1,
            'b': 2,
            'c': 4
        }
        self.assertEqual(expected, dict(self.any1.iteritems()))

    def testIteritemsAll(self):
        expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
        self.assertEqual(expected, list(self.any1.iteritems(all=True)))

    def testKeys(self):
        self.assertEqual(sorted(['a', 'b', 'c']), sorted(self.any1.keys()))
    
    def testIterkeys(self):
        self.assertEqual(sorted(['a', 'b', 'c']), sorted(self.any1.iterkeys()))
    
    def testSlotname(self):
        self.assertEqual('a', self.any1.slotname(0))
        self.assertEqual('b', self.any1.slotname(1))
        self.assertEqual('c', self.any1.slotname(3))
        self.assertEqual(None, self.any1.slotname(2))
        self.assertRaises(IndexError, self.any1.slotname, 5)

    def testStr(self):
        any2 = Anything([1, 2, 3, 4])
        self.any1['d'] = any2
        expected = """{
	/a 1
	/b 2
	3
	/c 4
	5
	/d {
		1
		2
		3
		4
	}
}"""
        self.assertEqual(expected, str(self.any1))
        
    def testRepr(self):
        expected = "Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])"
        result = repr(self.any1)
        self.assertEqual(expected, result)
        any2 = eval(result)
        self.assertEqual(1, self.any1['a'])
        self.assertEqual(2, self.any1['b'])
        self.assertEqual(4, self.any1['c'])
        self.assertEqual(1, self.any1[0])
        self.assertEqual(2, self.any1[1])
        self.assertEqual(3, self.any1[2])
        self.assertEqual(4, self.any1[3])
        self.assertEqual(5, self.any1[4])
        
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
    
    def testInsert(self):
        self.any1.insert(2, 'new')
        self.assertEqual(6, len(self.any1))
        self.assertEqual(1, self.any1[0])
        self.assertEqual(2, self.any1[1])
        self.assertEqual('new', self.any1[2])
        self.assertEqual(3, self.any1[3])
        self.assertEqual(4, self.any1[4])
        self.assertEqual(5, self.any1[5])
        self.assertEqual(1, self.any1['a'])
        self.assertEqual(2, self.any1['b'])
        self.assertEqual(4, self.any1['c'])

    def testDeleteWithPos(self):
        del self.any1[0]
        self.assertEqual(4, len(self.any1))
        self.assertEqual(2, self.any1[0])
        self.assertEqual(3, self.any1[1])
        self.assertEqual(4, self.any1[2])
        self.assertEqual(5, self.any1[3])
        self.assertEqual(2, self.any1['b'])        
        self.assertEqual(4, self.any1['c'])
        self.assertEqual(None, self.any1.get('a', None))
        
    def testDeleteWithKey(self):
        del self.any1['a']
        self.assertEqual(4, len(self.any1))
        self.assertEqual(2, self.any1[0])
        self.assertEqual(3, self.any1[1])
        self.assertEqual(4, self.any1[2])
        self.assertEqual(5, self.any1[3])
        self.assertEqual(2, self.any1['b'])
        self.assertEqual(4, self.any1['c'])
        self.assertEqual(None, self.any1.get('a', None))
        
    def testUpdateWithDict(self):
        self.any1.update({'a': 99, 'b': 88, 'd': 77})
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])

    def testUpdateWithAnything(self):
        any2 = Anything()
        any2['a'] = 99
        any2['b'] = 88
        any2['d'] = 77
        self.any1.update(any2)
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])

    def testExtendWithList(self):
        self.any1.extend([55, ('d', 66), 77])
        self.assertEqual(Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]), self.any1)

    def testExtendWithAnything(self):
        self.any1.extend(Anything([55, ('d', 66), 77]))
        self.assertEqual(Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]), self.any1)

    def testAddAnything(self):
        self.any1 += Anything([55, ('d', 66), 77])
        self.assertEqual(Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]), self.any1)

    def testAddList(self):
        self.any1 += [55, ('d', 66), 77]
        self.assertEqual(Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]), self.any1)

    def testAddReturnsCopy(self):
        any1before = self.any1.copy()
        any2 = self.any1 + Anything([55, ('d', 66), 77])
        self.assertEqual(any1before, self.any1)
        self.assertEqual(Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]), any2)

    def testMergeWithAnything(self):
        any2 = Anything()
        any2['a'] = 99
        any2.append(66)
        any2['b'] = 88
        any2['d'] = 77
        any2.append(55)
        self.any1.merge(any2)
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(66, self.any1[5])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])
        self.assertEqual(55, self.any1[7])

    def testMergeWithDict(self):
        self.any1.merge({'a': 99, 'b': 88, 'd': 77})
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])
        
    def testMergeWithList(self):
        self.any1.merge([('a', 99), 66, ('b', 88), ('d', 77), 55])
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(66, self.any1[5])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])
        self.assertEqual(55, self.any1[7])
        
    def testInitWithDict(self):
        any2 = Anything({'a': 99, 'b': 88, 'd': 77})
        self.assertEqual(3, len(any2))
        self.assertEqual(99, any2['a'])
        self.assertEqual(88, any2['b'])
        self.assertEqual(77, any2['d'])
        
    def testInitWithKW(self):
        any2 = Anything(a=99, b=88, d=77)
        self.assertEqual(3, len(any2))
        self.assertEqual(99, any2['a'])
        self.assertEqual(88, any2['b'])
        self.assertEqual(77, any2['d'])
        
    def testInitWithAnything(self):
        any2 = Anything(self.any1)
        self.assertEqual(1, any2['a'])
        self.assertEqual(2, any2['b'])
        self.assertEqual(4, any2['c'])
        self.assertEqual(1, any2[0])
        self.assertEqual(2, any2[1])
        self.assertEqual(3, any2[2])
        self.assertEqual(4, any2[3])
        self.assertEqual(5, any2[4])
        
    def testInitWithList(self):
        any2 = Anything([('a', 99), 66, ('b', 88), ('d', 77), 55])
        self.assertEqual(99, any2['a'])
        self.assertEqual(66, any2[1])
        self.assertEqual(88, any2['b'])
        self.assertEqual(77, any2['d'])
        self.assertEqual(55, any2[4])

    def testPop(self):
        value = self.any1.pop('a')
        self.assertEqual(1, value)
        self.assertEqual(4, len(self.any1))
        self.assertEqual(None, self.any1.get('a', None))
        self.assertRaises(KeyError, self.any1.pop, 'a')
    
    def testPopitem(self):
        data = self.any1.popitem()
        self.assertEqual(4, len(self.any1))
        self.assertEqual(('a', 1), data)
        data = self.any1.popitem()
        self.assertEqual(3, len(self.any1))
        self.assertEqual(('b', 2), data)
        data = self.any1.popitem()
        self.assertEqual(2, len(self.any1))
        self.assertEqual((None, 3), data)
        data = self.any1.popitem()
        self.assertEqual(1, len(self.any1))
        self.assertEqual(('c', 4), data)
        data = self.any1.popitem()
        self.assertEqual(0, len(self.any1))
        self.assertEqual((None, 5), data)
        self.assertRaises(KeyError, self.any1.popitem)

    def testEq(self):
        any2 = Anything()
        any2['a'] = 1
        any2['b'] = 2
        any2.append(3)
        any2['c'] = 4
        any2.append(5)
        self.assertEqual(self.any1, any2)

    def testCopy(self):
        any2 = self.any1.copy()
        self.assertNotEqual(id(any2), id(self.any1))
        self.assertEqual(self.any1, any2)
        
    def testGetSlice(self):
        any2 = self.any1[1:3]
        self.assertEqual(Anything([('b', 2), 3]), any2)

    def testDelSlice(self):
        del self.any1[1:3]
        self.assertEqual(Anything([('a', 1), ('c', 4), 5]), self.any1)
        self.assertEqual(None, self.any1.get('b', None))
        self.assertEqual(4, self.any1['c'])
        
    def testSetSliceWithAnything(self):
        self.any1[1:3] = Anything([99, ('d', 88)])
        self.assertEqual(Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]), self.any1)
        
    def testSetSliceWithList(self):
        self.any1[1:3] = [99, ('d', 88)]
        self.assertEqual(Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]), self.any1)

    def testReverse(self):
        self.any1.reverse()
        self.assertEqual(Anything([5, ('c', 4), 3, ('b', 2), ('a', 1)]), self.any1)

    def testIndex(self):
        for i in xrange(1,5):
            print i
            self.assertEqual(i-1, self.any1.index(i))

    def testCount(self):
        self.any1.extend([2 ,3 ,3])
        self.assertEqual(1, self.any1.count(1))
        self.assertEqual(2, self.any1.count(2))
        self.assertEqual(3, self.any1.count(3))
        self.assertEqual(1, self.any1.count(4))
        self.assertEqual(1, self.any1.count(5))

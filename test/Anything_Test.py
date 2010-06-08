import unittest, os, tempfile, shutil
from Anything import *

class AnythingTest(unittest.TestCase):
    def setUp(self):
        self.any1 = Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])

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
        result = repr(self.any1)
        self.assertEqual("Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])", result)
        self.assertEqual(self.any1, eval(result))

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

    def testSort(self):
        any2 = Anything([('e',7),3,5,('a',2),('b',1), ('c', 1), 4])
        any2.sort()
        self.assertEqual(Anything([('b',1),('c',1),('a',2),3,4,5,('e',7)]), any2)
        self.assertEqual(7, any2['e'])
        self.assertEqual(1, any2['c'])
        self.assertEqual(1, any2['b'])
        self.assertEqual(2, any2['a'])

class AnythingParserTest(unittest.TestCase):
    def testParse(self):
        content = """
dd
  {
	bla
	"blub dd"
	12
    /key va3lue#comment
    /"a nice key" value
    {
    	ggg
    	xs
    }
 { dsfd dds }
/blub { 
  sdfsd sdf
  ddd
   }}dsfsdf
   {
   second 
   }
   {
   1
   2
   3.0
   } sdfdsf !
   """
        result = parse(content)
        expected = [
                    Anything(['bla',
                             'blub dd',
                             12,
                             ('key', 'va3lue'),
                             ('a nice key', 'value'),
                             Anything(['ggg', 'xs']),
                             Anything(['dsfd', 'dds']),
                             ('blub', Anything(['sdfsd', 'sdf', 'ddd']))
                             ]),
                    Anything(['second']),
                    Anything([1, 2, 3.0])
                   ]
        self.assertEqual(expected, result)

class ResolvePathTest(unittest.TestCase):
    def __makeTempFile(self, filename, relpath=None):
        if relpath:
            path = os.path.join(self.tempdir, relpath)
            os.makedirs(path)
        else:
            path = self.tempdir
        os.mknod(os.path.join(path, filename))

    def setUp(self):
        self.savedPath = os.getcwd()
        self.savedEnviron = os.environ.copy()
        self.tempdir = tempfile.mkdtemp()
        self.__makeTempFile('test1.any')
        self.__makeTempFile('test2.any', 'config')
        self.__makeTempFile('test3.any', 'src')
        self.__makeTempFile('test4.any', 'test')

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        os.chdir(self.savedPath)
        os.environ = self.savedEnviron
        setLocalEnv({})

    def testResolveAbs(self):
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))
        self.assertEqual(os.path.join(self.tempdir, 'test1.any'), resolvePath(os.path.join(self.tempdir, "test1.any")))

    def testResolveCwd(self):
        os.chdir(self.tempdir)
        self.assertEqual(os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any"))
        self.assertEqual(os.path.join(self.tempdir, 'config', 'test2.any'), resolvePath("test2.any"))
        self.assertEqual(os.path.join(self.tempdir, 'src', 'test3.any'), resolvePath("test3.any"))
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))

    def testResolvePathEnv(self):
        os.environ['WD_ROOT'] = self.tempdir
        self.assertEqual(os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any"))
        self.assertEqual(os.path.join(self.tempdir, 'config', 'test2.any'), resolvePath("test2.any"))
        self.assertEqual(os.path.join(self.tempdir, 'src', 'test3.any'), resolvePath("test3.any"))
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))
        os.environ['WD_PATH'] = '.:config:src:test'
        self.assertEqual(os.path.join(self.tempdir, 'test', 'test4.any'), resolvePath("test4.any"))

    def testResolvePathTLS(self):
        setLocalEnv({'WD_ROOT': self.tempdir})
        self.assertEqual(os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any"))
        self.assertEqual(os.path.join(self.tempdir, 'config', 'test2.any'), resolvePath("test2.any"))
        self.assertEqual(os.path.join(self.tempdir, 'src', 'test3.any'), resolvePath("test3.any"))
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))
        setLocalEnv(WD_PATH='.:config:src:test')
        self.assertEqual(os.path.join(self.tempdir, 'test', 'test4.any'), resolvePath("test4.any"))

    def testResolvePathPassed(self):
        self.assertEqual(os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any", self.tempdir))
        self.assertEqual(os.path.join(self.tempdir, 'config', 'test2.any'), resolvePath("test2.any", self.tempdir))
        self.assertEqual(os.path.join(self.tempdir, 'src', 'test3.any'), resolvePath("test3.any", self.tempdir))
        self.assertRaises(IOError, lambda: resolvePath("test4.any", self.tempdir))
        self.assertEqual(os.path.join(self.tempdir, 'test', 'test4.any'),
                         resolvePath("test4.any", self.tempdir, '.:config:src:test'))
        self.assertEqual(os.path.join(self.tempdir, 'test', 'test4.any'),
                         resolvePath("test4.any", self.tempdir, ['.','config','src','test']))

class UtilsTest(unittest.TestCase):
    def testFirst(self):
        result = first([lambda: None, lambda: 2, lambda: 3])
        self.assertEqual(2, result)
    
    def testFirstWithArg(self):
        result = first([lambda arg: None, lambda arg: arg, lambda arg: 3], 42)
        self.assertEqual(42, result)
        
    def testToNumber(self):
        self.assertEqual(42, toNumber("42"))
        self.assertEqual(42.0, toNumber("42.0"))
        self.assertEqual("42.0a", toNumber("42.0a"))
        
    def testLoadAllFromFile(self):
        result = loadAllFromFile(resolvePath('AnythingLoadFromFileTest.any', os.path.dirname(__file__), 'data'))
        expected = [
                    Anything([('key', 'value')])
                   ]
        self.assertEqual(expected, result)

    def testLoadFromFile(self):
        result = loadFromFile(resolvePath('AnythingLoadFromFileTest.any', os.path.dirname(__file__), 'data'))
        expected = Anything([('key', 'value')])
        self.assertEqual(expected, result)

class AnythingReferenceTest(unittest.TestCase):
    def setUp(self):
        self.any1 = Anything([('a', 1), ('b', 2), 3, ('c', Anything([('a', Anything([1, 2, 3]))])), 5])
        self.savedEnviron = os.environ.copy()
        os.environ['WD_ROOT'] = os.path.dirname(__file__)
        os.environ['WD_PATH'] = '.:data'

    def tearDown(self):
        os.environ = self.savedEnviron

    def testInternalKey(self):
        anyref1 = parseRef('%a')
        self.assertEqual(1, anyref1.resolve(self.any1))

    def testInternalIndex(self):
        anyref1 = parseRef('%:1')
        self.assertEqual(2, anyref1.resolve(self.any1))

    def testInternalCombined(self):
        anyref1 = parseRef('%c.a:0')
        self.assertEqual(1, anyref1.resolve(self.any1))

    def testExternal(self):
        expected = 'include works'
        anyref1 = parseRef('!AnythingReferenceTest2.any?test')
        self.assertEqual(expected, anyref1.resolve())
        anyref1 = parseRef('!file:///AnythingReferenceTest2.any?test')
        self.assertEqual(expected, anyref1.resolve())
        anyref1 = parseRef('!file://dummyhost/AnythingReferenceTest2.any?test')
        self.assertEqual(expected, anyref1.resolve())
        anyref2 = parseRef('!AnythingReferenceTest2.any?struct')
        expected = Anything([1, 2, 3])
        self.assertEqual(expected, anyref2.resolve())

    def testInternalFromFile(self):
        anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
        self.assertEqual(1, anys["ref1"])
        self.assertEqual(4, anys["ref2"])
        self.assertEqual('d2', anys["ref3"])

    def testExternalFromFile(self):
        anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
        self.assertEqual('include works', anys["ref4"])

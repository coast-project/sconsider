# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import unittest
import os
import tempfile
import shutil
from Anything import *


class TestAnything(unittest.TestCase):
    def setUp(self):
        self.any1 = Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])

    def test_Len(self):
        self.assertEqual(5, len(self.any1))

    def test_Content(self):
        self.assertEqual(1, self.any1['a'])
        self.assertEqual(2, self.any1['b'])
        self.assertEqual(4, self.any1['c'])
        self.assertEqual(1, self.any1[0])
        self.assertEqual(2, self.any1[1])
        self.assertEqual(3, self.any1[2])
        self.assertEqual(4, self.any1[3])
        self.assertEqual(5, self.any1[4])

    def test_SetWithPos(self):
        self.any1[0] = 99
        self.assertEqual(99, self.any1['a'])

    def test_SetWithKey(self):
        self.any1['a'] = 99
        self.assertEqual(99, self.any1[0])

    def test_ArrayIteration(self):
        expected = map(lambda i: i + 1, range(5))
        self.assertEqual(expected, [v for v in self.any1])

    def test_Itervalues(self):
        expected = [1, 2, 4]
        self.assertEqual(sorted(expected), sorted(list(self.any1.itervalues())))

    def test_ItervaluesAll(self):
        expected = map(lambda i: i + 1, range(5))
        self.assertEqual(expected, list(self.any1.itervalues(all_items=True)))

    def test_Values(self):
        expected = [1, 2, 4]
        self.assertEqual(sorted(expected), sorted(list(self.any1.values())))

    def test_ValuesAll(self):
        expected = map(lambda i: i + 1, range(5))
        self.assertEqual(expected, list(self.any1.values(all_items=True)))

    def test_Items(self):
        expected = {'a': 1, 'b': 2, 'c': 4}
        self.assertEqual(expected, dict(self.any1.items()))

    def test_ItemsAll(self):
        expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
        self.assertEqual(expected, self.any1.items(all_items=True))

    def test_Iteritems(self):
        expected = {'a': 1, 'b': 2, 'c': 4}
        self.assertEqual(expected, dict(self.any1.iteritems()))

    def test_IteritemsAll(self):
        expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
        self.assertEqual(expected, list(self.any1.iteritems(all_items=True)))

    def test_Keys(self):
        self.assertEqual(sorted(['a', 'b', 'c']), sorted(self.any1.keys()))

    def test_Iterkeys(self):
        self.assertEqual(sorted(['a', 'b', 'c']), sorted(self.any1.iterkeys()))

    def test_Slotname(self):
        self.assertEqual('a', self.any1.slotname(0))
        self.assertEqual('b', self.any1.slotname(1))
        self.assertEqual('c', self.any1.slotname(3))
        self.assertEqual(None, self.any1.slotname(2))
        self.assertRaises(IndexError, self.any1.slotname, 5)

    def test_Str(self):
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

    def test_Repr(self):
        result = repr(self.any1)
        self.assertEqual("Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])",
                         result)
        self.assertEqual(self.any1, eval(result))

    def test_HasKey(self):
        self.assertTrue(self.any1.has_key('a'))
        self.assertTrue(self.any1.has_key('b'))
        self.assertTrue(self.any1.has_key('c'))
        self.assertFalse(self.any1.has_key('d'))

    def test_Contains(self):
        for i in xrange(1, 5):
            self.assertTrue(i in self.any1)
        self.assertFalse(0 in self.any1)
        self.assertTrue(6 not in self.any1)

    def test_Insert(self):
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

    def test_DeleteWithPos(self):
        del self.any1[0]
        self.assertEqual(4, len(self.any1))
        self.assertEqual(2, self.any1[0])
        self.assertEqual(3, self.any1[1])
        self.assertEqual(4, self.any1[2])
        self.assertEqual(5, self.any1[3])
        self.assertEqual(2, self.any1['b'])
        self.assertEqual(4, self.any1['c'])
        self.assertEqual(None, self.any1.get('a', None))

    def test_DeleteWithKey(self):
        del self.any1['a']
        self.assertEqual(4, len(self.any1))
        self.assertEqual(2, self.any1[0])
        self.assertEqual(3, self.any1[1])
        self.assertEqual(4, self.any1[2])
        self.assertEqual(5, self.any1[3])
        self.assertEqual(2, self.any1['b'])
        self.assertEqual(4, self.any1['c'])
        self.assertEqual(None, self.any1.get('a', None))

    def test_UpdateWithDict(self):
        self.any1.update({'a': 99, 'b': 88, 'd': 77})
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])

    def test_UpdateWithAnything(self):
        any2 = Anything()
        any2['a'] = 99
        any2['b'] = 88
        any2['d'] = 77
        self.any1.update(any2)
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])

    def test_ExtendWithList(self):
        self.any1.extend([55, ('d', 66), 77])
        self.assertEqual(
            Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]),
            self.any1)

    def test_ExtendWithAnything(self):
        self.any1.extend(Anything([55, ('d', 66), 77]))
        self.assertEqual(
            Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]),
            self.any1)

    def test_AddAnything(self):
        self.any1 += Anything([55, ('d', 66), 77])
        self.assertEqual(
            Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]),
            self.any1)

    def test_AddList(self):
        self.any1 += [55, ('d', 66), 77]
        self.assertEqual(
            Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]),
            self.any1)

    def test_AddReturnsCopy(self):
        any1before = self.any1.copy()
        any2 = self.any1 + Anything([55, ('d', 66), 77])
        self.assertEqual(any1before, self.any1)
        self.assertEqual(
            Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]),
            any2)

    def test_MergeWithAnything(self):
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

    def test_MergeWithDict(self):
        self.any1.merge({'a': 99, 'b': 88, 'd': 77})
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])

    def test_MergeWithList(self):
        self.any1.merge([('a', 99), 66, ('b', 88), ('d', 77), 55])
        self.assertEqual(99, self.any1['a'])
        self.assertEqual(66, self.any1[5])
        self.assertEqual(88, self.any1['b'])
        self.assertEqual(77, self.any1['d'])
        self.assertEqual(55, self.any1[7])

    def test_InitWithDict(self):
        any2 = Anything({'a': 99, 'b': 88, 'd': 77})
        self.assertEqual(3, len(any2))
        self.assertEqual(99, any2['a'])
        self.assertEqual(88, any2['b'])
        self.assertEqual(77, any2['d'])

    def test_InitWithKW(self):
        any2 = Anything(a=99, b=88, d=77)
        self.assertEqual(3, len(any2))
        self.assertEqual(99, any2['a'])
        self.assertEqual(88, any2['b'])
        self.assertEqual(77, any2['d'])

    def test_InitWithAnything(self):
        any2 = Anything(self.any1)
        self.assertEqual(1, any2['a'])
        self.assertEqual(2, any2['b'])
        self.assertEqual(4, any2['c'])
        self.assertEqual(1, any2[0])
        self.assertEqual(2, any2[1])
        self.assertEqual(3, any2[2])
        self.assertEqual(4, any2[3])
        self.assertEqual(5, any2[4])

    def test_InitWithList(self):
        any2 = Anything([('a', 99), 66, ('b', 88), ('d', 77), 55])
        self.assertEqual(99, any2['a'])
        self.assertEqual(66, any2[1])
        self.assertEqual(88, any2['b'])
        self.assertEqual(77, any2['d'])
        self.assertEqual(55, any2[4])

    def test_Pop(self):
        value = self.any1.pop('a')
        self.assertEqual(1, value)
        self.assertEqual(4, len(self.any1))
        self.assertEqual(None, self.any1.get('a', None))
        self.assertRaises(KeyError, self.any1.pop, 'a')

    def test_Popitem(self):
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

    def test_Eq(self):
        any2 = Anything()
        any2['a'] = 1
        any2['b'] = 2
        any2.append(3)
        any2['c'] = 4
        any2.append(5)
        self.assertEqual(self.any1, any2)

    def test_Copy(self):
        any2 = self.any1.copy()
        self.assertNotEqual(id(any2), id(self.any1))
        self.assertEqual(self.any1, any2)

    def test_GetSlice(self):
        any2 = self.any1[1:3]
        self.assertEqual(Anything([('b', 2), 3]), any2)

    def test_DelSlice(self):
        del self.any1[1:3]
        self.assertEqual(Anything([('a', 1), ('c', 4), 5]), self.any1)
        self.assertEqual(None, self.any1.get('b', None))
        self.assertEqual(4, self.any1['c'])

    def test_SetSliceWithAnything(self):
        self.any1[1:3] = Anything([99, ('d', 88)])
        self.assertEqual(
            Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]), self.any1)

    def test_SetSliceWithList(self):
        self.any1[1:3] = [99, ('d', 88)]
        self.assertEqual(
            Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]), self.any1)

    def test_Reverse(self):
        self.any1.reverse()
        self.assertEqual(
            Anything([5, ('c', 4), 3, ('b', 2), ('a', 1)]), self.any1)

    def test_Index(self):
        for i in xrange(1, 5):
            print i
            self.assertEqual(i - 1, self.any1.index(i))

    def test_Count(self):
        self.any1.extend([2, 3, 3])
        self.assertEqual(1, self.any1.count(1))
        self.assertEqual(2, self.any1.count(2))
        self.assertEqual(3, self.any1.count(3))
        self.assertEqual(1, self.any1.count(4))
        self.assertEqual(1, self.any1.count(5))

    def test_Sort(self):
        any2 = Anything([('e', 7), 3, 5, ('a', 2), ('b', 1), ('c', 1), 4])
        any2.sort()
        self.assertEqual(
            Anything([('b', 1), ('c', 1), ('a', 2), 3, 4, 5, ('e', 7)]), any2)
        self.assertEqual(7, any2['e'])
        self.assertEqual(1, any2['c'])
        self.assertEqual(1, any2['b'])
        self.assertEqual(2, any2['a'])


class TestAnythingParser(unittest.TestCase):
    def test_Parse(self):
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
            Anything(['bla', 'blub dd', 12, ('key', 'va3lue'),
                      ('a nice key', 'value'), Anything(['ggg', 'xs']),
                      Anything(['dsfd', 'dds']),
                      ('blub', Anything(['sdfsd', 'sdf', 'ddd']))]),
            Anything(['second']), Anything([1, 2, 3.0])
        ]
        self.assertEqual(expected, result)


class TestResolvePath(unittest.TestCase):
    def __makeTempFile(self, filename, relpath=None):
        if relpath:
            path = os.path.join(self.tempdir, relpath)
            os.makedirs(path)
        else:
            path = self.tempdir
        with open(os.path.join(path, filename), 'w') as file:
            file.write('{ dummy }')

    def setUp(self):
        self.savedPath = os.getcwd()
        self.savedEnviron = os.environ.copy()
        self.tempdir = tempfile.mkdtemp()
        self.__makeTempFile('test1.any')
        self.__makeTempFile('test2.any', 'config')
        self.__makeTempFile('test3.any', 'src')
        self.__makeTempFile('test4.any', 'test')

    def tearDown(self):
        os.chdir(self.savedPath)
        shutil.rmtree(self.tempdir)
        os.environ = self.savedEnviron
        setLocalEnv({})

    def test_ResolveAbs(self):
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'test1.any'),
            resolvePath(os.path.join(self.tempdir, "test1.any")))

    def test_ResolveCwd(self):
        os.chdir(self.tempdir)
        self.assertEqual(
            os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'config', 'test2.any'),
            resolvePath("test2.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'src', 'test3.any'),
            resolvePath("test3.any"))
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))

    def test_ResolvePathEnv(self):
        os.environ['COAST_ROOT'] = self.tempdir
        self.assertEqual(
            os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'config', 'test2.any'),
            resolvePath("test2.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'src', 'test3.any'),
            resolvePath("test3.any"))
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))
        os.environ['COAST_PATH'] = '.:config:src:test'
        self.assertEqual(
            os.path.join(self.tempdir, 'test', 'test4.any'),
            resolvePath("test4.any"))

    def test_ResolvePathTLS(self):
        setLocalEnv({'COAST_ROOT': self.tempdir})
        self.assertEqual(
            os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'config', 'test2.any'),
            resolvePath("test2.any"))
        self.assertEqual(
            os.path.join(self.tempdir, 'src', 'test3.any'),
            resolvePath("test3.any"))
        self.assertRaises(IOError, lambda: resolvePath("test4.any"))
        setLocalEnv(COAST_PATH='.:config:src:test')
        self.assertEqual(
            os.path.join(self.tempdir, 'test', 'test4.any'),
            resolvePath("test4.any"))

    def test_ResolvePathPassed(self):
        self.assertEqual(
            os.path.join(self.tempdir, 'test1.any'), resolvePath("test1.any",
                                                                 self.tempdir))
        self.assertEqual(
            os.path.join(self.tempdir, 'config', 'test2.any'),
            resolvePath("test2.any", self.tempdir))
        self.assertEqual(
            os.path.join(self.tempdir, 'src', 'test3.any'),
            resolvePath("test3.any", self.tempdir))
        self.assertRaises(IOError,
                          lambda: resolvePath("test4.any", self.tempdir))
        self.assertEqual(
            os.path.join(self.tempdir, 'test', 'test4.any'),
            resolvePath("test4.any", self.tempdir, '.:config:src:test'))
        self.assertEqual(
            os.path.join(self.tempdir, 'test', 'test4.any'),
            resolvePath("test4.any", self.tempdir, [
                '.', 'config', 'src', 'test'
            ]))


class TestUtils(unittest.TestCase):
    def test_First(self):
        result = first([lambda: None, lambda: 2, lambda: 3])
        self.assertEqual(2, result)

    def test_FirstWithArg(self):
        result = first([lambda arg: None, lambda arg: arg, lambda arg: 3], 42)
        self.assertEqual(42, result)

    def test_ToNumber(self):
        self.assertEqual(42, toNumber("42"))
        self.assertEqual(42.0, toNumber("42.0"))
        self.assertEqual("42.0a", toNumber("42.0a"))

    def test_LoadAllFromFile(self):
        result = loadAllFromFile(resolvePath('AnythingLoadFromFileTest.any',
                                             os.path.dirname(__file__), 'data'))
        expected = [Anything([('key', 'value')])]
        self.assertEqual(expected, result)

    def test_LoadFromFile(self):
        result = loadFromFile(resolvePath('AnythingLoadFromFileTest.any',
                                          os.path.dirname(__file__), 'data'))
        expected = Anything([('key', 'value')])
        self.assertEqual(expected, result)

    def test_LoadFromNonexistingFile(self):
        self.assertRaises(
            IOError,
            lambda: loadFromFile(
                os.path.join(
                    os.path.dirname(__file__),
                    'data',
                    'NotThere.any')))
        result = None
        try:
            result = loadFromFile(os.path.join(
                os.path.dirname(__file__), 'data', 'NotThere.any'))
        except IOError:
            pass
        self.assertEqual(None, result)


class TestAnythingReference(unittest.TestCase):
    def setUp(self):
        self.any1 = Anything([('a', 1), ('b', 2), 3,
                              ('c', Anything([('a', Anything([1, 2, 3]))])), 5,
                              ('a.b:3', 'escaped')])
        self.savedEnviron = os.environ.copy()
        os.environ['COAST_ROOT'] = os.path.dirname(__file__)
        os.environ['COAST_PATH'] = '.:data'

    def tearDown(self):
        os.environ = self.savedEnviron

    def test_InternalKey(self):
        anyref1 = parseRef('%a')
        self.assertEqual(1, anyref1.resolve(self.any1))

    def test_InternalIndex(self):
        anyref1 = parseRef('%:1')
        self.assertEqual(2, anyref1.resolve(self.any1))

    def test_InternalCombined(self):
        anyref1 = parseRef('%c.a:0')
        self.assertEqual(1, anyref1.resolve(self.any1))

    def test_InternalEscaped(self):
        anyref1 = parseRef('%a\.b\:3')
        self.assertEqual('escaped', anyref1.resolve(self.any1))

    def test_External(self):
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

    def test_InternalFromFile(self):
        anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
        self.assertEqual(1, anys["ref1"])
        self.assertEqual(4, anys["ref2"])
        self.assertEqual('d2', anys["ref3"])

    def test_ExternalFromFile(self):
        anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
        self.assertEqual('include works', anys["ref4"])

# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import pytest
import os
import tempfile
import shutil
from Anything import *


class TestAnything(object):
    def setup_method(self, method):
        self.any1 = Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])

    def test_Len(self):
        assert 5 == len(self.any1)

    def test_Content(self):
        assert 1 == self.any1['a']
        assert 2 == self.any1['b']
        assert 4 == self.any1['c']
        assert 1 == self.any1[0]
        assert 2 == self.any1[1]
        assert 3 == self.any1[2]
        assert 4 == self.any1[3]
        assert 5 == self.any1[4]

    def test_SetWithPos(self):
        self.any1[0] = 99
        assert 99 == self.any1['a']

    def test_SetWithKey(self):
        self.any1['a'] = 99
        assert 99 == self.any1[0]

    def test_ArrayIteration(self):
        expected = map(lambda i: i + 1, range(5))
        assert expected == [v for v in self.any1]

    def test_Itervalues(self):
        expected = [1, 2, 4]
        assert sorted(expected) == sorted(list(self.any1.itervalues()))

    def test_ItervaluesAll(self):
        expected = map(lambda i: i + 1, range(5))
        assert expected == list(self.any1.itervalues(all_items=True))

    def test_Values(self):
        expected = [1, 2, 4]
        assert sorted(expected) == sorted(list(self.any1.values()))

    def test_ValuesAll(self):
        expected = map(lambda i: i + 1, range(5))
        assert expected == list(self.any1.values(all_items=True))

    def test_Items(self):
        expected = {'a': 1, 'b': 2, 'c': 4}
        assert expected == dict(self.any1.items())

    def test_ItemsAll(self):
        expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
        assert expected == self.any1.items(all_items=True)

    def test_Iteritems(self):
        expected = {'a': 1, 'b': 2, 'c': 4}
        assert expected == dict(self.any1.iteritems())

    def test_IteritemsAll(self):
        expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
        assert expected == list(self.any1.iteritems(all_items=True))

    def test_Keys(self):
        assert sorted(['a', 'b', 'c']) == sorted(self.any1.keys())

    def test_Iterkeys(self):
        assert sorted(['a', 'b', 'c']) == sorted(self.any1.iterkeys())

    def test_Slotname(self):
        assert 'a' == self.any1.slotname(0)
        assert 'b' == self.any1.slotname(1)
        assert 'c' == self.any1.slotname(3)
        assert None == self.any1.slotname(2)
        with pytest.raises(IndexError):
            self.any1.slotname(5)

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
        assert expected == str(self.any1)

    def test_Repr(self):
        result = repr(self.any1)
        assert "Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])" == result
        assert self.any1 == eval(result)

    def test_HasKey(self):
        assert self.any1.has_key('a')
        assert self.any1.has_key('b')
        assert self.any1.has_key('c')
        assert not self.any1.has_key('d')

    def test_Contains(self):
        for i in xrange(1, 5):
            assert i in self.any1
        assert 0 not in self.any1
        assert 6 not in self.any1

    def test_Insert(self):
        self.any1.insert(2, 'new')
        assert 6 == len(self.any1)
        assert 1 == self.any1[0]
        assert 2 == self.any1[1]
        assert 'new' == self.any1[2]
        assert 3 == self.any1[3]
        assert 4 == self.any1[4]
        assert 5 == self.any1[5]
        assert 1 == self.any1['a']
        assert 2 == self.any1['b']
        assert 4 == self.any1['c']

    def test_DeleteWithPos(self):
        del self.any1[0]
        assert 4 == len(self.any1)
        assert 2 == self.any1[0]
        assert 3 == self.any1[1]
        assert 4 == self.any1[2]
        assert 5 == self.any1[3]
        assert 2 == self.any1['b']
        assert 4 == self.any1['c']
        assert None == self.any1.get('a', None)

    def test_DeleteWithKey(self):
        del self.any1['a']
        assert 4 == len(self.any1)
        assert 2 == self.any1[0]
        assert 3 == self.any1[1]
        assert 4 == self.any1[2]
        assert 5 == self.any1[3]
        assert 2 == self.any1['b']
        assert 4 == self.any1['c']
        assert None == self.any1.get('a', None)

    def test_UpdateWithDict(self):
        self.any1.update({'a': 99, 'b': 88, 'd': 77})
        assert 99 == self.any1['a']
        assert 88 == self.any1['b']
        assert 77 == self.any1['d']

    def test_UpdateWithAnything(self):
        any2 = Anything()
        any2['a'] = 99
        any2['b'] = 88
        any2['d'] = 77
        self.any1.update(any2)
        assert 99 == self.any1['a']
        assert 88 == self.any1['b']
        assert 77 == self.any1['d']

    def test_ExtendWithList(self):
        self.any1.extend([55, ('d', 66), 77])
        assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55,
                         ('d', 66), 77]) == self.any1

    def test_ExtendWithAnything(self):
        self.any1.extend(Anything([55, ('d', 66), 77]))
        assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55,
                         ('d', 66), 77]) == self.any1

    def test_AddAnything(self):
        self.any1 += Anything([55, ('d', 66), 77])
        assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55,
                         ('d', 66), 77]) == self.any1

    def test_AddList(self):
        self.any1 += [55, ('d', 66), 77]
        assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55,
                         ('d', 66), 77]) == self.any1

    def test_AddReturnsCopy(self):
        any1before = self.any1.copy()
        any2 = self.any1 + Anything([55, ('d', 66), 77])
        assert any1before == self.any1
        assert Anything(
            [('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]) == any2

    def test_MergeWithAnything(self):
        any2 = Anything()
        any2['a'] = 99
        any2.append(66)
        any2['b'] = 88
        any2['d'] = 77
        any2.append(55)
        self.any1.merge(any2)
        assert 99 == self.any1['a']
        assert 66 == self.any1[5]
        assert 88 == self.any1['b']
        assert 77 == self.any1['d']
        assert 55 == self.any1[7]

    def test_MergeWithDict(self):
        self.any1.merge({'a': 99, 'b': 88, 'd': 77})
        assert 99 == self.any1['a']
        assert 88 == self.any1['b']
        assert 77 == self.any1['d']

    def test_MergeWithList(self):
        self.any1.merge([('a', 99), 66, ('b', 88), ('d', 77), 55])
        assert 99 == self.any1['a']
        assert 66 == self.any1[5]
        assert 88 == self.any1['b']
        assert 77 == self.any1['d']
        assert 55 == self.any1[7]

    def test_InitWithDict(self):
        any2 = Anything({'a': 99, 'b': 88, 'd': 77})
        assert 3 == len(any2)
        assert 99 == any2['a']
        assert 88 == any2['b']
        assert 77 == any2['d']

    def test_InitWithKW(self):
        any2 = Anything(a=99, b=88, d=77)
        assert 3 == len(any2)
        assert 99 == any2['a']
        assert 88 == any2['b']
        assert 77 == any2['d']

    def test_InitWithAnything(self):
        any2 = Anything(self.any1)
        assert 1 == any2['a']
        assert 2 == any2['b']
        assert 4 == any2['c']
        assert 1 == any2[0]
        assert 2 == any2[1]
        assert 3 == any2[2]
        assert 4 == any2[3]
        assert 5 == any2[4]

    def test_InitWithList(self):
        any2 = Anything([('a', 99), 66, ('b', 88), ('d', 77), 55])
        assert 99 == any2['a']
        assert 66 == any2[1]
        assert 88 == any2['b']
        assert 77 == any2['d']
        assert 55 == any2[4]

    def test_Pop(self):
        value = self.any1.pop('a')
        assert 1 == value
        assert 4 == len(self.any1)
        assert None == self.any1.get('a', None)
        with pytest.raises(KeyError):
            self.any1.pop('a')

    def test_Popitem(self):
        data = self.any1.popitem()
        assert 4 == len(self.any1)
        assert ('a', 1) == data
        data = self.any1.popitem()
        assert 3 == len(self.any1)
        assert ('b', 2) == data
        data = self.any1.popitem()
        assert 2 == len(self.any1)
        assert (None, 3) == data
        data = self.any1.popitem()
        assert 1 == len(self.any1)
        assert ('c', 4) == data
        data = self.any1.popitem()
        assert 0 == len(self.any1)
        assert (None, 5) == data
        with pytest.raises(KeyError):
            self.any1.popitem()

    def test_Eq(self):
        any2 = Anything()
        any2['a'] = 1
        any2['b'] = 2
        any2.append(3)
        any2['c'] = 4
        any2.append(5)
        assert self.any1 == any2

    def test_Copy(self):
        any2 = self.any1.copy()
        assert id(any2) != id(self.any1)
        assert self.any1 == any2

    def test_GetSlice(self):
        any2 = self.any1[1:3]
        assert Anything([('b', 2), 3]) == any2

    def test_DelSlice(self):
        del self.any1[1:3]
        assert Anything([('a', 1), ('c', 4), 5]) == self.any1
        assert None == self.any1.get('b', None)
        assert 4 == self.any1['c']

    def test_SetSliceWithAnything(self):
        self.any1[1:3] = Anything([99, ('d', 88)])
        assert Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]) == self.any1

    def test_SetSliceWithList(self):
        self.any1[1:3] = [99, ('d', 88)]
        assert Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]) == self.any1

    def test_Reverse(self):
        self.any1.reverse()
        assert Anything([5, ('c', 4), 3, ('b', 2), ('a', 1)]) == self.any1

    def test_Index(self):
        for i in xrange(1, 5):
            print i
            assert i - 1 == self.any1.index(i)

    def test_Count(self):
        self.any1.extend([2, 3, 3])
        assert 1 == self.any1.count(1)
        assert 2 == self.any1.count(2)
        assert 3 == self.any1.count(3)
        assert 1 == self.any1.count(4)
        assert 1 == self.any1.count(5)

    def test_Sort(self):
        any2 = Anything([('e', 7), 3, 5, ('a', 2), ('b', 1), ('c', 1), 4])
        any2.sort()
        assert Anything(
            [('b', 1), ('c', 1), ('a', 2), 3, 4, 5, ('e', 7)]) == any2
        assert 7 == any2['e']
        assert 1 == any2['c']
        assert 1 == any2['b']
        assert 2 == any2['a']


class TestAnythingParser(object):
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
        assert expected == result


class TestResolvePath(object):
    def __makeTempFile(self, filename, relpath=None):
        if relpath:
            path = os.path.join(self.tempdir, relpath)
            os.makedirs(path)
        else:
            path = self.tempdir
        with open(os.path.join(path, filename), 'w') as file:
            file.write('{ dummy }')

    def setup_method(self, method):
        self.savedPath = os.getcwd()
        self.savedEnviron = os.environ.copy()
        self.tempdir = tempfile.mkdtemp()
        self.__makeTempFile('test1.any')
        self.__makeTempFile('test2.any', 'config')
        self.__makeTempFile('test3.any', 'src')
        self.__makeTempFile('test4.any', 'test')

    def teardown_method(self, method):
        os.chdir(self.savedPath)
        shutil.rmtree(self.tempdir)
        os.environ = self.savedEnviron
        setLocalEnv({})

    def test_ResolveAbs(self):
        with pytest.raises(IOError):
            resolvePath("test4.any")
        assert os.path.join(
            self.tempdir,
            'test1.any') == resolvePath(os.path.join(self.tempdir, "test1.any"))

    def test_ResolveCwd(self):
        os.chdir(self.tempdir)
        assert os.path.join(self.tempdir,
                            'test1.any') == resolvePath("test1.any")
        assert os.path.join(self.tempdir, 'config',
                            'test2.any') == resolvePath("test2.any")
        assert os.path.join(self.tempdir, 'src',
                            'test3.any') == resolvePath("test3.any")
        with pytest.raises(IOError):
            resolvePath("test4.any")

    def test_ResolvePathEnv(self):
        os.environ['COAST_ROOT'] = self.tempdir
        assert os.path.join(self.tempdir,
                            'test1.any') == resolvePath("test1.any")
        assert os.path.join(self.tempdir, 'config',
                            'test2.any') == resolvePath("test2.any")
        assert os.path.join(self.tempdir, 'src',
                            'test3.any') == resolvePath("test3.any")
        with pytest.raises(IOError):
            resolvePath("test4.any")
        os.environ['COAST_PATH'] = '.:config:src:test'
        assert os.path.join(self.tempdir, 'test',
                            'test4.any') == resolvePath("test4.any")

    def test_ResolvePathTLS(self):
        setLocalEnv({'COAST_ROOT': self.tempdir})
        assert os.path.join(self.tempdir,
                            'test1.any') == resolvePath("test1.any")
        assert os.path.join(self.tempdir, 'config',
                            'test2.any') == resolvePath("test2.any")
        assert os.path.join(self.tempdir, 'src',
                            'test3.any') == resolvePath("test3.any")
        with pytest.raises(IOError):
            resolvePath("test4.any")
        setLocalEnv(COAST_PATH='.:config:src:test')
        assert os.path.join(self.tempdir, 'test',
                            'test4.any') == resolvePath("test4.any")

    def test_ResolvePathPassed(self):
        assert os.path.join(self.tempdir, 'test1.any') == resolvePath(
            "test1.any", self.tempdir)
        assert os.path.join(self.tempdir, 'config', 'test2.any') == resolvePath(
            "test2.any", self.tempdir)
        assert os.path.join(self.tempdir, 'src', 'test3.any') == resolvePath(
            "test3.any", self.tempdir)
        with pytest.raises(IOError):
            resolvePath("test4.any", self.tempdir)
        assert os.path.join(self.tempdir, 'test', 'test4.any') == resolvePath(
            "test4.any", self.tempdir, '.:config:src:test')
        assert os.path.join(self.tempdir, 'test', 'test4.any') == resolvePath(
            "test4.any", self.tempdir, [
                '.', 'config', 'src', 'test'
            ])


class TestUtils(object):
    def test_First(self):
        result = first([lambda: None, lambda: 2, lambda: 3])
        assert 2 == result

    def test_FirstWithArg(self):
        result = first([lambda arg: None, lambda arg: arg, lambda arg: 3], 42)
        assert 42 == result

    def test_ToNumber(self):
        assert 42 == toNumber("42")
        assert 42.0 == toNumber("42.0")
        assert "42.0a" == toNumber("42.0a")

    def test_LoadAllFromFile(self):
        result = loadAllFromFile(resolvePath('AnythingLoadFromFileTest.any',
                                             os.path.dirname(__file__), 'data'))
        expected = [Anything([('key', 'value')])]
        assert expected == result

    def test_LoadFromFile(self):
        result = loadFromFile(resolvePath('AnythingLoadFromFileTest.any',
                                          os.path.dirname(__file__), 'data'))
        expected = Anything([('key', 'value')])
        assert expected == result

    def test_LoadFromNonexistingFile(self):
        with pytest.raises(IOError):
            loadFromFile(os.path.join(
                os.path.dirname(__file__), 'data', 'NotThere.any'))
        result = None
        try:
            result = loadFromFile(os.path.join(
                os.path.dirname(__file__), 'data', 'NotThere.any'))
        except IOError:
            pass
        assert None == result


class TestAnythingReference(object):
    def setup_method(self, method):
        self.any1 = Anything([('a', 1), ('b', 2), 3,
                              ('c', Anything([('a', Anything([1, 2, 3]))])), 5,
                              ('a.b:3', 'escaped')])
        self.savedEnviron = os.environ.copy()
        os.environ['COAST_ROOT'] = os.path.dirname(__file__)
        os.environ['COAST_PATH'] = '.:data'

    def teardown_method(self, method):
        os.environ = self.savedEnviron

    def test_InternalKey(self):
        anyref1 = parseRef('%a')
        assert 1 == anyref1.resolve(self.any1)

    def test_InternalIndex(self):
        anyref1 = parseRef('%:1')
        assert 2 == anyref1.resolve(self.any1)

    def test_InternalCombined(self):
        anyref1 = parseRef('%c.a:0')
        assert 1 == anyref1.resolve(self.any1)

    def test_InternalEscaped(self):
        anyref1 = parseRef('%a\.b\:3')
        assert 'escaped' == anyref1.resolve(self.any1)

    def test_External(self):
        expected = 'include works'
        anyref1 = parseRef('!AnythingReferenceTest2.any?test')
        assert expected == anyref1.resolve()
        anyref1 = parseRef('!file:///AnythingReferenceTest2.any?test')
        assert expected == anyref1.resolve()
        anyref1 = parseRef('!file://dummyhost/AnythingReferenceTest2.any?test')
        assert expected == anyref1.resolve()
        anyref2 = parseRef('!AnythingReferenceTest2.any?struct')
        expected = Anything([1, 2, 3])
        assert expected == anyref2.resolve()

    def test_InternalFromFile(self):
        anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
        assert 1 == anys["ref1"]
        assert 4 == anys["ref2"]
        assert 'd2' == anys["ref3"]

    def test_ExternalFromFile(self):
        anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
        assert 'include works' == anys["ref4"]

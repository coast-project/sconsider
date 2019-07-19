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
from Anything import Anything, parseRef, loadFromFile, loadAllFromFile, resolvePath, first, toNumber, parse, setLocalEnv


@pytest.fixture
def any1():
    """Predefined Anything with values."""
    return Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])


@pytest.fixture
def any2(monkeypatch):
    """Predefined Anything with values."""
    monkeypatch.setenv('COAST_ROOT', os.path.dirname(__file__))
    monkeypatch.setenv('COAST_PATH', '.:data')
    return Anything([('a', 1), ('b', 2), 3, ('c', Anything([('a', Anything([1, 2, 3]))])), 5,
                     ('a.b:3', 'escaped')])


def test_AnythingLen(any1):
    assert 5 == len(any1)


def test_AnythingContent(any1):
    assert 1 == any1['a']
    assert 2 == any1['b']
    assert 4 == any1['c']
    assert 1 == any1[0]
    assert 2 == any1[1]
    assert 3 == any1[2]
    assert 4 == any1[3]
    assert 5 == any1[4]


def test_AnythingSetWithPos(any1):
    any1[0] = 99
    assert 99 == any1['a']


def test_AnythingSetWithKey(any1):
    any1['a'] = 99
    assert 99 == any1[0]


def test_AnythingArrayIteration(any1):
    expected = map(lambda i: i + 1, range(5))
    assert expected == [v for v in any1]


def test_AnythingItervalues(any1):
    expected = [1, 2, 4]
    assert sorted(expected) == sorted(list(any1.itervalues()))


def test_AnythingItervaluesAll(any1):
    expected = map(lambda i: i + 1, range(5))
    assert expected == list(any1.itervalues(all_items=True))


def test_AnythingValues(any1):
    expected = [1, 2, 4]
    assert sorted(expected) == sorted(list(any1.values()))


def test_AnythingValuesAll(any1):
    expected = map(lambda i: i + 1, range(5))
    assert expected == list(any1.values(all_items=True))


def test_AnythingItems(any1):
    expected = {'a': 1, 'b': 2, 'c': 4}
    assert expected == dict(any1.items())


def test_AnythingItemsAll(any1):
    expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
    assert expected == any1.items(all_items=True)


def test_AnythingIteritems(any1):
    expected = {'a': 1, 'b': 2, 'c': 4}
    assert expected == dict(any1.iteritems())


def test_AnythingIteritemsAll(any1):
    expected = [('a', 1), ('b', 2), (None, 3), ('c', 4), (None, 5)]
    assert expected == list(any1.iteritems(all_items=True))


def test_AnythingKeys(any1):
    assert sorted(['a', 'b', 'c']) == sorted(any1.keys())


def test_AnythingIterkeys(any1):
    assert sorted(['a', 'b', 'c']) == sorted(any1.iterkeys())


def test_AnythingSlotname(any1):
    assert 'a' == any1.slotname(0)
    assert 'b' == any1.slotname(1)
    assert 'c' == any1.slotname(3)
    assert None is any1.slotname(2)
    with pytest.raises(IndexError):
        any1.slotname(5)


def test_AnythingStr(any1):
    any2 = Anything([1, 2, 3, 4])
    any1['d'] = any2
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
    assert expected == str(any1)


def test_AnythingRepr(any1):
    result = repr(any1)
    assert "Anything([('a', 1), ('b', 2), 3, ('c', 4), 5])" == result
    assert any1 == eval(result)


def test_AnythingHasKey(any1):
    assert any1.has_key('a')
    assert any1.has_key('b')
    assert any1.has_key('c')
    assert not any1.has_key('d')


def test_AnythingContains(any1):
    for i in xrange(1, 5):
        assert i in any1
    assert 0 not in any1
    assert 6 not in any1


def test_AnythingInsert(any1):
    any1.insert(2, 'new')
    assert 6 == len(any1)
    assert 1 == any1[0]
    assert 2 == any1[1]
    assert 'new' == any1[2]
    assert 3 == any1[3]
    assert 4 == any1[4]
    assert 5 == any1[5]
    assert 1 == any1['a']
    assert 2 == any1['b']
    assert 4 == any1['c']


def test_AnythingDeleteWithPos(any1):
    del any1[0]
    assert 4 == len(any1)
    assert 2 == any1[0]
    assert 3 == any1[1]
    assert 4 == any1[2]
    assert 5 == any1[3]
    assert 2 == any1['b']
    assert 4 == any1['c']
    assert None is any1.get('a', None)


def test_AnythingDeleteWithKey(any1):
    del any1['a']
    assert 4 == len(any1)
    assert 2 == any1[0]
    assert 3 == any1[1]
    assert 4 == any1[2]
    assert 5 == any1[3]
    assert 2 == any1['b']
    assert 4 == any1['c']
    assert None is any1.get('a', None)


def test_AnythingUpdateWithDict(any1):
    any1.update({'a': 99, 'b': 88, 'd': 77})
    assert 99 == any1['a']
    assert 88 == any1['b']
    assert 77 == any1['d']


def test_AnythingUpdateWithAnything(any1):
    any2 = Anything()
    any2['a'] = 99
    any2['b'] = 88
    any2['d'] = 77
    any1.update(any2)
    assert 99 == any1['a']
    assert 88 == any1['b']
    assert 77 == any1['d']


def test_AnythingExtendWithList(any1):
    any1.extend([55, ('d', 66), 77])
    assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]) == any1


def test_AnythingExtendWithAnything(any1):
    any1.extend(Anything([55, ('d', 66), 77]))
    assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]) == any1


def test_AnythingAddAnything(any1):
    any1 += Anything([55, ('d', 66), 77])
    assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]) == any1


def test_AnythingAddList(any1):
    any1 += [55, ('d', 66), 77]
    assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]) == any1


def test_AnythingAddReturnsCopy(any1):
    any1before = any1.copy()
    any2 = any1 + Anything([55, ('d', 66), 77])
    assert any1before == any1
    assert Anything([('a', 1), ('b', 2), 3, ('c', 4), 5, 55, ('d', 66), 77]) == any2


def test_AnythingMergeWithAnything(any1):
    any2 = Anything()
    any2['a'] = 99
    any2.append(66)
    any2['b'] = 88
    any2['d'] = 77
    any2.append(55)
    any1.merge(any2)
    assert 99 == any1['a']
    assert 66 == any1[5]
    assert 88 == any1['b']
    assert 77 == any1['d']
    assert 55 == any1[7]


def test_AnythingMergeWithDict(any1):
    any1.merge({'a': 99, 'b': 88, 'd': 77})
    assert 99 == any1['a']
    assert 88 == any1['b']
    assert 77 == any1['d']


def test_AnythingMergeWithList(any1):
    any1.merge([('a', 99), 66, ('b', 88), ('d', 77), 55])
    assert 99 == any1['a']
    assert 66 == any1[5]
    assert 88 == any1['b']
    assert 77 == any1['d']
    assert 55 == any1[7]


def test_AnythingInitWithDict(any1):
    any2 = Anything({'a': 99, 'b': 88, 'd': 77})
    assert 3 == len(any2)
    assert 99 == any2['a']
    assert 88 == any2['b']
    assert 77 == any2['d']


def test_AnythingInitWithKW(any1):
    any2 = Anything(a=99, b=88, d=77)
    assert 3 == len(any2)
    assert 99 == any2['a']
    assert 88 == any2['b']
    assert 77 == any2['d']


def test_AnythingInitWithAnything(any1):
    any2 = Anything(any1)
    assert 1 == any2['a']
    assert 2 == any2['b']
    assert 4 == any2['c']
    assert 1 == any2[0]
    assert 2 == any2[1]
    assert 3 == any2[2]
    assert 4 == any2[3]
    assert 5 == any2[4]


def test_AnythingInitWithList(any1):
    any2 = Anything([('a', 99), 66, ('b', 88), ('d', 77), 55])
    assert 99 == any2['a']
    assert 66 == any2[1]
    assert 88 == any2['b']
    assert 77 == any2['d']
    assert 55 == any2[4]


def test_AnythingPop(any1):
    value = any1.pop('a')
    assert 1 == value
    assert 4 == len(any1)
    assert None is any1.get('a', None)
    with pytest.raises(KeyError):
        any1.pop('a')


def test_AnythingPopitem(any1):
    data = any1.popitem()
    assert 4 == len(any1)
    assert ('a', 1) == data
    data = any1.popitem()
    assert 3 == len(any1)
    assert ('b', 2) == data
    data = any1.popitem()
    assert 2 == len(any1)
    assert (None, 3) == data
    data = any1.popitem()
    assert 1 == len(any1)
    assert ('c', 4) == data
    data = any1.popitem()
    assert 0 == len(any1)
    assert (None, 5) == data
    with pytest.raises(KeyError):
        any1.popitem()


def test_AnythingEq(any1):
    any2 = Anything()
    any2['a'] = 1
    any2['b'] = 2
    any2.append(3)
    any2['c'] = 4
    any2.append(5)
    assert any1 == any2


def test_AnythingCopy(any1):
    any2 = any1.copy()
    assert id(any2) != id(any1)
    assert any1 == any2


def test_AnythingGetSlice(any1):
    any2 = any1[1:3]
    assert Anything([('b', 2), 3]) == any2


def test_AnythingDelSlice(any1):
    del any1[1:3]
    assert Anything([('a', 1), ('c', 4), 5]) == any1
    assert None is any1.get('b', None)
    assert 4 == any1['c']


def test_AnythingSetSliceWithAnything(any1):
    any1[1:3] = Anything([99, ('d', 88)])
    assert Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]) == any1


def test_AnythingSetSliceWithList(any1):
    any1[1:3] = [99, ('d', 88)]
    assert Anything([('a', 1), 99, ('d', 88), ('c', 4), 5]) == any1


def test_AnythingReverse(any1):
    any1.reverse()
    assert Anything([5, ('c', 4), 3, ('b', 2), ('a', 1)]) == any1


def test_AnythingIndex(any1):
    for i in xrange(1, 5):
        print i
        assert i - 1 == any1.index(i)


def test_AnythingCount(any1):
    any1.extend([2, 3, 3])
    assert 1 == any1.count(1)
    assert 2 == any1.count(2)
    assert 3 == any1.count(3)
    assert 1 == any1.count(4)
    assert 1 == any1.count(5)


def test_AnythingSort(any1):
    any2 = Anything([('e', 7), 3, 5, ('a', 2), ('b', 1), ('c', 1), 4])
    any2.sort()
    assert Anything([('b', 1), ('c', 1), ('a', 2), 3, 4, 5, ('e', 7)]) == any2
    assert 7 == any2['e']
    assert 1 == any2['c']
    assert 1 == any2['b']
    assert 2 == any2['a']


def test_AnythingParserParse():
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
        Anything([
            'bla', 'blub dd', 12, ('key', 'va3lue'), ('a nice key', 'value'),
            Anything(['ggg', 'xs']),
            Anything(['dsfd', 'dds']), ('blub', Anything(['sdfsd', 'sdf', 'ddd']))
        ]),
        Anything(['second']),
        Anything([1, 2, 3.0])
    ]
    assert expected == result


@pytest.fixture(scope='session')
def any_files_dir(tmpdir_factory):
    def write_to(filename, path=''):
        filepath = tmpdir_factory.getbasetemp()
        if path:
            filepath = tmpdir_factory.mktemp(path, numbered=False)
        with open(os.path.join(str(filepath), filename), 'w') as file:
            file.write('{ dummy }')

    write_to('test1.any')
    write_to('test2.any', 'config')
    write_to('test3.any', 'src')
    write_to('test4.any', 'test')
    return str(tmpdir_factory.getbasetemp())


def test_ResolvePathAbs(any_files_dir):
    with pytest.raises(IOError):
        resolvePath("test4.any")
    assert os.path.join(any_files_dir, 'test1.any') == resolvePath(os.path.join(any_files_dir, "test1.any"))


def test_ResolvePathCwd(any_files_dir, monkeypatch):
    monkeypatch.chdir(any_files_dir)
    assert os.path.join(any_files_dir, 'test1.any') == resolvePath("test1.any")
    assert os.path.join(any_files_dir, 'config', 'test2.any') == resolvePath("test2.any")
    assert os.path.join(any_files_dir, 'src', 'test3.any') == resolvePath("test3.any")
    with pytest.raises(IOError):
        resolvePath("test4.any")


def test_ResolvePathEnv(any_files_dir, monkeypatch):
    monkeypatch.setenv('COAST_ROOT', any_files_dir)
    assert os.path.join(any_files_dir, 'test1.any') == resolvePath("test1.any")
    assert os.path.join(any_files_dir, 'config', 'test2.any') == resolvePath("test2.any")
    assert os.path.join(any_files_dir, 'src', 'test3.any') == resolvePath("test3.any")
    with pytest.raises(IOError):
        resolvePath("test4.any")
    monkeypatch.setenv('COAST_PATH', '.:config:src:test')
    assert os.path.join(any_files_dir, 'test', 'test4.any') == resolvePath("test4.any")


def test_ResolvePathTLS(any_files_dir, monkeypatch):
    setLocalEnv({'COAST_ROOT': any_files_dir})
    assert os.path.join(any_files_dir, 'test1.any') == resolvePath("test1.any")
    assert os.path.join(any_files_dir, 'config', 'test2.any') == resolvePath("test2.any")
    assert os.path.join(any_files_dir, 'src', 'test3.any') == resolvePath("test3.any")
    with pytest.raises(IOError):
        resolvePath("test4.any")
    setLocalEnv(COAST_PATH='.:config:src:test')
    assert os.path.join(any_files_dir, 'test', 'test4.any') == resolvePath("test4.any")
    setLocalEnv({})


def test_ResolvePathPassed(any_files_dir, monkeypatch):
    assert os.path.join(any_files_dir, 'test1.any') == resolvePath("test1.any", any_files_dir)
    assert os.path.join(any_files_dir, 'config', 'test2.any') == resolvePath("test2.any", any_files_dir)
    assert os.path.join(any_files_dir, 'src', 'test3.any') == resolvePath("test3.any", any_files_dir)
    with pytest.raises(IOError):
        resolvePath("test4.any", any_files_dir)
    assert os.path.join(any_files_dir, 'test', 'test4.any') == resolvePath("test4.any", any_files_dir,
                                                                           '.:config:src:test')
    assert os.path.join(any_files_dir, 'test', 'test4.any') == resolvePath("test4.any", any_files_dir,
                                                                           ['.', 'config', 'src', 'test'])


def test_UtilsFirst():
    result = first([lambda: None, lambda: 2, lambda: 3])
    assert 2 == result


def test_UtilsFirstWithArg():
    result = first([lambda arg: None, lambda arg: arg, lambda arg: 3], 42)
    assert 42 == result


def test_UtilsToNumber():
    assert 42 == toNumber("42")
    assert 42.0 == toNumber("42.0")
    assert "42.0a" == toNumber("42.0a")


def test_UtilsLoadAllFromFile():
    result = loadAllFromFile(resolvePath('AnythingLoadFromFileTest.any', os.path.dirname(__file__), 'data'))
    expected = [Anything([('key', 'value')])]
    assert expected == result


def test_UtilsLoadFromFile():
    result = loadFromFile(resolvePath('AnythingLoadFromFileTest.any', os.path.dirname(__file__), 'data'))
    expected = Anything([('key', 'value')])
    assert expected == result


def test_UtilsLoadFromNonexistingFile():
    with pytest.raises(IOError):
        loadFromFile(os.path.join(os.path.dirname(__file__), 'data', 'NotThere.any'))
    result = None
    try:
        result = loadFromFile(os.path.join(os.path.dirname(__file__), 'data', 'NotThere.any'))
    except IOError:
        pass
    assert None is result


def test_AnythingReferenceInternalKey(any2):
    anyref1 = parseRef('%a')
    assert 1 == anyref1.resolve(any2)


def test_AnythingReferenceInternalIndex(any2):
    anyref1 = parseRef('%:1')
    assert 2 == anyref1.resolve(any2)


def test_AnythingReferenceInternalCombined(any2):
    anyref1 = parseRef('%c.a:0')
    assert 1 == anyref1.resolve(any2)


def test_AnythingReferenceInternalEscaped(any2):
    anyref1 = parseRef('%a\.b\:3')
    assert 'escaped' == anyref1.resolve(any2)


def test_AnythingReferenceExternal(any2):
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


def test_AnythingReferenceInternalFromFile(any2):
    anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
    assert 1 == anys["ref1"]
    assert 4 == anys["ref2"]
    assert 'd2' == anys["ref3"]


def test_AnythingReferenceExternalFromFile(any2):
    anys = loadFromFile(resolvePath('AnythingReferenceTest.any'))
    assert 'include works' == anys["ref4"]

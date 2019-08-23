"""SConsider.Anything.

Utility module to parse Anything files and provide a python, dict-based,
equivalent
"""
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2010, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------
import collections
import operator
import threading
import os
from lepl.matchers.core import Literal, Regexp, Delayed, Any
from lepl.matchers.derived import Optional, Word, AnyBut, Integer, Newline,\
    Whitespace, String, Star
from lepl.matchers.combine import And
from lepl.matchers.operators import Separator


class AnythingEntry(object):
    def __init__(self, key, value=None):
        if isinstance(key, AnythingEntry):
            self.key = key.key
            self.value = key.value
        elif isinstance(key, tuple):
            self.key, self.value = key
        else:
            self.key = key
            self.value = value

    def get_value(self):
        if isinstance(self.__value, AnythingReference):
            return self.__value.resolve()
        return self.__value

    def set_value(self, newvalue):
        self.__value = newvalue

    value = property(get_value, set_value)

    def __eq__(self, other):
        return isinstance(other, AnythingEntry) and self.key == other.key and self.value == other.value

    def __str__(self):
        return '(' + str(self.key) + ', ' + str(self.value) + ')'

    def __repr__(self):
        return 'AnythingEntry(' + str(self.key) + ', ' + str(self.value) + ')'


class Anything(collections.MutableSequence, collections.MutableMapping):
    def __init__(self, other=None, **kw):
        self.__data = []
        self.__keys = {}
        if other:
            self.merge(other)
        elif kw:
            self.merge(kw)

    def insert(self, pos, value):
        self.__data.insert(pos, AnythingEntry(None, value))
        self.__updateKeys(pos + 1)

    def update(self, other):
        if isinstance(other, Anything):
            for key, value in other.iteritems():
                self[key] = value
        else:
            super(Anything, self).update(other)

    def extend(self, other):
        return self.merge(other)

    def merge(self, other):
        if isinstance(other, Anything):
            for data in other.iteritems(all_items=True):
                self.__mergeData(data)
        if isinstance(other, collections.Mapping):
            for data in other.iteritems():
                self.__mergeData(data)
        else:
            for data in other:
                self.__mergeData(data)
        return self

    def __mergeData(self, data):
        if isinstance(data, AnythingEntry):
            if data.key:
                self[data.key] = data.value
            else:
                self.append(data.value)
        elif isinstance(data, tuple):
            if isinstance(data[0], basestring):
                self[data[0]] = data[1]
            else:
                self.append(data[1])
        else:
            self.append(data)

    def __updateKeys(self, fromPos=0):
        for pos, data in enumerate(self.__data[fromPos:], fromPos):
            if data.key:
                self.__keys[data.key] = pos

    def clear(self):
        self.__data.clear()
        self.__keys.clear()

    def __delslice(self, theslice):
        start, stop, step = theslice.indices(len(self))
        for data in self.__data[start:stop:step]:
            if data.key:
                del self.__keys[data.key]
        del self.__data[start:stop:step]
        self.__updateKeys(start)

    def __delitem__(self, key):
        if isinstance(key, slice):
            return self.__delslice(key)
        elif isinstance(key, basestring):
            if key in self.__keys:
                pos = self.__keys[key]
                del self.__data[pos]
                del self.__keys[key]
                self.__updateKeys(pos)
        else:
            if self.__data[key].key:
                del self.__keys[self.__data[key].key]
            del self.__data[key]
            self.__updateKeys(key)

    def __getslice(self, theslice):
        start, stop, step = theslice.indices(len(self))
        return Anything(self.__data[start:stop:step])

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__getslice(key)
        elif isinstance(key, basestring):
            return self.__data[self.__keys[key]].value
        else:
            return self.__data[key].value

    def __len__(self):
        return len(self.__data)

    def __setslice(self, theslice, other):
        start, stop, step = theslice.indices(len(self))
        for data in self.__data[start:stop:step]:
            if data.key:
                del self.__keys[data.key]
        if isinstance(other, Anything):
            self.__data[start:stop:step] = [
                AnythingEntry(key, value) for key, value in other.items(all_items=True)
            ]
        elif isinstance(other, collections.Sequence):
            self.__data[start:stop:step] = [
                AnythingEntry(key, value) for key, value in Anything(other).items(all_items=True)
            ]
        self.__updateKeys(start)

    def __setitem__(self, key, value):
        if isinstance(value, AnythingReference):
            value.context = self
        if isinstance(key, slice):
            self.__setslice(key, value)
        elif isinstance(key, basestring):
            if key in self.__keys:
                self.__data[self.__keys[key]] = AnythingEntry(key, value)
            else:
                self.__keys[key] = len(self.__data)
                self.__data.append(AnythingEntry(key, value))
        else:
            self.__data[key] = AnythingEntry(key, value)

    def keys(self):
        return self.__keys.keys()

    def iterkeys(self):
        return self.__keys.iterkeys()

    def items(self, all_items=False):
        if all_items:
            return [(self.slotname(pos), value) for pos, value in enumerate(self)]
        else:
            return [(key, self.__data[pos].value) for key, pos in self.__keys.iteritems()]

    def iteritems(self, all_items=False):
        if all_items:
            for pos, value in enumerate(self):
                yield (self.slotname(pos), value)
        else:
            for key, pos in self.__keys.iteritems():
                yield (key, self.__data[pos].value)

    def itervalues(self, all_items=False):
        if all_items:
            for value in self:
                yield value
        else:
            for _, pos in self.__keys.iteritems():
                yield self.__data[pos].value

    def values(self, all_items=False):
        if all_items:
            return list(self)
        else:
            return [self.__data[pos].value for _, pos in self.__keys.iteritems()]

    def popitem(self):
        try:
            key, value = next(self.iteritems(all_items=True))
        except StopIteration:
            raise KeyError
        del self[0]
        return (key, value)

    def slotname(self, pos):
        if self.__data[pos].key:
            return self.__data[pos].key
        else:
            return None

    def has_key(self, key):
        return key in self.__keys

    def __pprint(self, level=1):
        content = ''
        for key, value in self.iteritems(all_items=True):
            content += '\t' * level
            if key:
                content += '/' + str(key) + ' '
            if isinstance(value, Anything):
                content += value.__pprint(level + 1) + '\n'
            else:
                content += str(value) + '\n'
        return '{\n' + content + ('\t' * (level - 1)) + '}'

    def __str__(self):
        return self.__pprint()

    def __repr__(self):
        return 'Anything(' + str([data if data[0] else data[1]
                                  for data in self.iteritems(all_items=True)]) + ')'

    def copy(self):
        return Anything(self)

    def reverse(self):
        self.__data.reverse()
        self.__updateKeys()

    def __eq__(self, other):
        return isinstance(other, Anything) and self.items(all_items=True) == other.items(all_items=True)

    def __add__(self, other):
        return self.copy().extend(other)

    def __radd__(self, other):
        return self.copy().extend(other)

    def __iadd__(self, other):
        return self.extend(other)

    def sort(self):
        self.__data.sort(key=operator.attrgetter('value', 'key'))
        self.__updateKeys()


class AnythingReference(object):
    def __init__(self, keys, filename=None):
        self.keys = keys
        self.file = filename
        self.context = None

    def resolve(self, context=None):
        if not context:
            if self.file:
                context = loadFromFile(self.file)
                if isinstance(context, list):
                    context = context[0]
            elif self.context:
                context = self.context
            else:
                raise ValueError('context not set')

        for key in self.keys:
            context = context[key]
        return context

    def __str__(self):
        keystr = ''
        for key in self.keys:
            if isinstance(key, int):
                keystr += ':'
            elif keystr:
                keystr += '.'
            keystr += str(key)

        if self.file:
            result = '!' + self.file
            if keystr:
                result += '?'
        else:
            result = '%'

        result += keystr

        if ' ' in result:
            return result[0] + '"' + result[1:] + '"'
        return result

    def __repr__(self):
        return 'AnythingReference(' + repr(self.keys) + (", '" + self.file + "'" if self.file else '') + ')'


class TLS(threading.local):
    def __init__(self):
        self.env = {}


tls = TLS()


def setLocalEnv(env=None, **kw):
    """Use env to set the entire env: setLocalEnv({'COAST_ROOT':

    '/path/to/dir'}) Use kw to add/update single values:
    setLocalEnv(COAST_PATH='.:config')
    """
    if env is not None:
        tls.env = env
    tls.env.update(kw)


resolvers = [
    lambda key: tls.env.get(key, None)
    if hasattr(tls, 'env') else None, lambda key: os.environ.get(key, None)
]


def first(funcs, *args, **kw):
    for func in funcs:
        result = func(*args, **kw)
        if result:
            return result
    return None


def resolvePath(filename, root=None, path=None):
    if os.path.isabs(filename):
        return filename

    if not root or not os.path.isdir(root):
        root = first(resolvers + [lambda key: os.getcwd()], 'COAST_ROOT')

    if not path:
        path = first(resolvers + [lambda key: ['.', 'config', 'src']], 'COAST_PATH')
    if isinstance(path, basestring):
        path = path.split(':')

    for rel in path:
        absfilepath = os.path.abspath(os.path.join(root, rel, filename))
        if os.path.isfile(absfilepath):
            return absfilepath
    raise IOError(filename)


anythingCache = {}
anythingCacheLock = threading.Lock()


def loadAllFromFile(filename):
    filename = resolvePath(filename)
    with anythingCacheLock:
        if filename not in anythingCache:
            with open(filename, "r") as f:
                anythingCache[filename] = parse(f.read())
        return anythingCache[filename]


def loadFromFile(filename):
    return loadAllFromFile(filename)[0]


def toNumber(string):
    try:
        return int(string) if string.isdigit() else float(string)
    except ValueError:
        return string


def createAnythingReferenceGrammar():
    indexstart = Literal(':')
    keystart = Literal('.')
    escape = Literal('\\')
    key = Optional(~keystart) & Word(And(~escape, keystart | indexstart) | AnyBut(keystart | indexstart))
    index = ~indexstart & Integer() >> int
    internalref = (key | index)[:] > list

    delimiter = Literal('?')
    filename = Word(AnyBut(delimiter))
    filedesc = Optional(~Regexp(r'file://[^/]*/')) & filename

    def reverse(alist):
        return list(reversed(alist))

    externalref = (filedesc & Optional(~delimiter & internalref)) >= reverse

    fullref = (~Literal('!') & externalref) | (~Literal('%') & internalref)
    return fullref


refgrammar = createAnythingReferenceGrammar()


def parseRef(refstring):
    return AnythingReference(*refgrammar.parse(refstring))


def createAnythingGrammar():
    commentstart = Literal('#')
    comment = ~commentstart & AnyBut(Newline())[:, ...] & ~Newline()
    anystart = Literal('{')
    anystop = Literal('}')
    word = Word(AnyBut(Whitespace() | anystart | anystop | commentstart))
    anything = Delayed()
    reference = (Literal('!') | Literal('%')) + (String() | word) >> parseRef
    stringvalue = String() | word >> toNumber
    value = anything | reference | stringvalue
    key = ~Literal('/') & (String() | word)
    keyvalue = Delayed()
    content = ~comment | keyvalue | value
    with Separator(~Star(Whitespace())):
        keyvalue += key & value > tuple
        anything += ~anystart & content[:] & ~anystop > Anything
    with Separator(~Star(AnyBut(anystart | anystop))):
        document = ~AnyBut(anystart)[:] & anything[:] & ~Any()[:]
    return document


anygrammar = createAnythingGrammar()


def parse(anythingstring):
    return anygrammar.parse(anythingstring)

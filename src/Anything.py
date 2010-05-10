import collections, operator
from lepl import *

class AnythingEntry(object):
    def __init__(self, key, value=None):
        if isinstance(key, AnythingEntry):
            self.key, key.key
            self.value = key.value
        elif isinstance(key, tuple):
            self.key, self.value = key
        else:
            self.key = key
            self.value = value
    
    def __eq__(self, other):
        return isinstance(other, AnythingEntry) and self.key == other.key and self.value == other.value

    def __str__(self):
        return '('+str(self.key)+', '+str(self.value)+')'

    def __repr__(self):
        return 'AnythingEntry('+str(self.key)+', '+str(self.value)+')'

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
        self.__updateKeys(pos+1)

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
            for data in other.iteritems(all=True):
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
            self.__data[start:stop:step] = [AnythingEntry(key, value) for key, value in other.items(all=True)]
        elif isinstance(other, collections.Sequence):
            self.__data[start:stop:step] = [AnythingEntry(key, value) for key, value in Anything(other).items(all=True)]
        self.__updateKeys(start)

    def __setitem__(self, key, value):
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

    def items(self, all=False):
        if all:
            return [(self.slotname(pos), value) for pos, value in enumerate(self)]
        else:
            return [(key, self.__data[pos].value) for key, pos in self.__keys.iteritems()]

    def iteritems(self, all=False):
        if all:
            for pos, value in enumerate(self):
                yield (self.slotname(pos), value)
        else:
            for key, pos in self.__keys.iteritems():
                yield (key, self.__data[pos].value)

    def itervalues(self, all=False):
        if all:
            for value in self:
                yield value
        else:
            for _, pos in self.__keys.iteritems():
                yield self.__data[pos].value

    def values(self, all=False):
        if all:
            return list(self)
        else:
            return [self.__data[pos].value for _, pos in self.__keys.iteritems()]

    def popitem(self):
        try:
            key, value = next(self.iteritems(all=True))
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
        for key, value in self.iteritems(all=True):
            content += '\t'*level
            if key:
                content += '/'+str(key)+' '
            if isinstance(value, Anything):
                content += value.__pprint(level+1)+'\n'
            else:
                content += str(value)+'\n'
        return '{\n'+content+('\t'*(level-1))+'}'
        
    def __str__(self):
        return self.__pprint()

    def __repr__(self):
        return 'Anything('+str(map(lambda data: data if data[0] else data[1], self.iteritems(all=True)))+')'

    def copy(self):
        return Anything(self)

    def reverse(self):
        self.__data.reverse()
        self.__updateKeys()

    def __eq__(self, other):
        return isinstance(other, Anything) and self.items(all=True) == other.items(all=True)

    def __add__(self, other):
        return self.copy().extend(other)

    def __radd__(self, other):
        return self.copy().extend(other)

    def __iadd__(self, other):
        return self.extend(other)
    
    def sort(self):
        self.__data.sort(key=operator.attrgetter('value', 'key'))
        self.__updateKeys()

def parse(content):
    commentstart = Literal('#')
    comment = ~commentstart & AnyBut('\n')[:,...] & ~Literal('\n')
    anystart = Literal('{')
    anystop = Literal('}')
    word = Word(AnyBut(Whitespace() | anystart | anystop | commentstart))
    anything = Delayed()
    anyvalue = anything | String() | word
    anykey = ~Literal('/') & ( String() | word )
    anykeyvalue = Delayed()
    anycontent = ~comment | anykeyvalue | anyvalue
    with Separator(~Star(Whitespace())):
        anykeyvalue += anykey & anyvalue > tuple
        anything += ~anystart & anycontent[:] & ~anystop > Anything
    with Separator(~Star(AnyBut(anystart | anystop))):
        document = ~AnyBut(anystart)[:] & anything[:] & ~Any()[:]
    return document.parse(content)


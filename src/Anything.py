import collections

class Anything(collections.MutableSequence, collections.MutableMapping):
	def __init__(self, other=None, **kw):
		self.__data = []
		self.__keys = {}
		if other:
			self.merge(other)
		elif kw:
			self.merge(kw)

	def insert(self, pos, value):
		self.__data.insert(pos, (None, value))
		self.__updateKeys(pos+1)
	
	def update(self, other):
		if isinstance(other, Anything):
			for key, value in other.iteritems():
				self[key] = value
		else:
			super(Anything, self).update(other)
			
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
				
	def __mergeData(self, data):
		if isinstance(data, tuple):
			if isinstance(data[0], str):
				self[data[0]] = data[1]
			else:
				self.append(data[1])
		else:
			self.append(data)

	def __updateKeys(self, fromPos=0):
		for pos, data in enumerate(self.__data[fromPos:], fromPos):
			if data[0]:
				self.__keys[data[0]] = pos
	
	def clear(self):
		self.__data.clear()
		self.__keys.clear()
	
	def __delitem__(self, key):
		if isinstance(key, str):
			if key in self.__keys:
				pos = self.__keys[key]
				del self.__data[pos]
				del self.__keys[key]
				self.__updateKeys(pos)
		else:
			if self.__data[key][0]:
				del self.__keys[self.__data[key][0]]
			del self.__data[key]
			self.__updateKeys(key)

	def __getslice(self, theslice):
		print theslice.start
		print theslice.stop
		print theslice.step
		print theslice.indices(5)

	def __getitem__(self, key):
		if isinstance(key, slice):
			return self.__getslice(key)
		elif isinstance(key, str):
			return self.__data[self.__keys[key]][1]
		else:
			return self.__data[key][1]
		
	def __len__(self):
		return len(self.__data)
		
	def __setitem__(self, key, value):
		if isinstance(key, str):
			if key in self.__keys:
				self.__data[self.__keys[key]] = (key, value)
			else:
				self.__keys[key] = len(self.__data)
				self.__data.append((key, value))
		else:
			self.__data[key] = (key, value)
	
	def keys(self):
		return self.__keys.keys()
	
	def iterkeys(self):
		return self.__keys.iterkeys()
		
	def items(self, all=False):
		if all:
			return [(self.slotname(pos), value) for pos, value in enumerate(self)]
		else:
			return [(key, self.__data[pos][1]) for key, pos in self.__keys.iteritems()]
		
	def iteritems(self, all=False):
		if all:
			for pos, value in enumerate(self):
				yield (self.slotname(pos), value)
		else:
			for key, pos in self.__keys.iteritems():
				yield (key, self.__data[pos][1])

	def itervalues(self, all=False):
		if all:
			for value in self:
				yield value
		else:
			for key, pos in self.__keys.iteritems():
				yield self.__data[pos][1]

	def values(self, all=False):
		if all:
			return list(self)
		else:
			return [self.__data[pos][1] for key, pos in self.__keys.iteritems()]

	def popitem(self):
		try:
			key, value = next(self.iteritems(all=True))
		except StopIteration:
			raise KeyError
		del self[0]
		return (key, value)
	
	def slotname(self, pos):
		if self.__data[pos][0]:
			return self.__data[pos][0]
		else:
			return None
	
	def has_key(self, key):
		return key in self.__keys
		
	def __str__(self):
		return str(map(lambda data: data if data[0] else data[1], self.iteritems(all=True)))

	def __repr__(self):
		return 'Anything('+str(self)+')'

	def copy(self):
		return Anything(self)

	def __eq__(self, other):
		return isinstance(other, Anything) and self.items(all=True) == other.items(all=True)


import collections

class Anything(collections.MutableSequence, collections.MutableMapping):
	def __init__(self):
		self.__data = []
		self.__keys = {}
	
	def insert(self, pos, value):
		self.__data.insert(pos, (None, value))
		self.__updateKeys(pos+1)
	
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
		
	def items(self):
		return [(key, self.__data[pos][1]) for key, pos in self.__keys.iteritems()]
		
	def iteritems(self):
		for key, pos in self.__keys.iteritems():
			yield (key, self.__data[pos][1])
	
	def slotname(self, pos):
		if self.__data[pos][0]:
			return self.__data[pos][0]
		else:
			return None
	
	def has_key(self, key):
		return key in self.__keys
		
	def __str__(self):
		string = '['
		for pos, data in enumerate(self.__data):
			if data[0]:
				string += str(data)
			else:
				string += str(data[1])
			if pos < len(self.__data)-1:
				string += ', '
		string += ']'
		return string


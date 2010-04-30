import collections

class Anything(collections.MutableSequence, collections.MutableMapping):
	def __init__(self):
		self.__data = []
		self.__keys = {}
	
	def insert(self, key, value):
		self.__data.insert(key, value)
		#TODO: reorder key ids!
	
	def clear(self):
		self.__data.clear()
		self.__keys.clear()
	
	def __delitem__(self, key):
		if isinstance(key, str):
			if key in self.__keys:
				del self.__data[self.__keys[key]]
				del self.__keys[key]
				#TODO: reorder key ids!
		else:
			del self.__data[key]
	
	def __getslice(self, theslice):
		print theslice.start
		print theslice.stop
		print theslice.step
		print theslice.indices(5)

	def __getitem__(self, key):
		if isinstance(key, slice):
			return self.__getslice(key)
		elif isinstance(key, str):
			return self.__data[self.__keys[key]]
		else:
			return self.__data[key]
		
	def __len__(self):
		return len(self.__data)
		
	def __setitem__(self, key, value):
		if isinstance(key, str):
			if key in self.__keys:
				self.__data[self.__keys[key]] = value
			else:
				self.__keys[key] = len(self.__data)
				self.__data.append(value)
		else:
			self.__data[key] = value
	
	def __str__(self):
		return str(self.__data)
		
	def keys(self):
		return self.__keys.keys()
	
	def iterkeys(self):
		return self.__keys.iterkeys()
		
	def items(self):
		return [(key, self[key]) for key in self.keys()]
		
	def iteritems(self):
		for key in self.iterkeys():
			yield (key, self[key])
	
	def slotname(self, pos):
		for k, p in self.__keys.iteritems():
			if p == pos:
				return k
		return None
	
	def has_key(self, key):
		return key in self.__keys


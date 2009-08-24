class Callback:
    def __init__(self):
        self.callbacks = {}

    def register(self, name, func, **kw):
        self.callbacks.setdefault(name, []).append((func, kw))
        
    def call(self, name, **overrides):
        for func, kw in self.callbacks.get(name, []):
            kw.update(overrides)
            func(**kw)
class Callback(object):
    def __init__(self):
        self.callbacks = {}

    def register(self, signalname, func, **kw):
        self.callbacks.setdefault(signalname, []).append((func, kw))
        
    def call(self, signalname, **overrides):
        for func, kw in self.callbacks.get(signalname, []):
            kw.update(overrides)
            func(**kw)

def addCallbackFeature(modulename):
    callback = Callback()

    def registerCallback(signalname, func, **kw):
        callback.register(signalname, func, **kw)

    def runCallback(signalname, **overrides):
        callback.call(signalname, **overrides)

    module = __import__(modulename)
    module.registerCallback = registerCallback
    module.runCallback = runCallback

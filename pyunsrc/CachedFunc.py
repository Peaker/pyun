from cPickle import dumps

class CachedFunc(object):
    def __init__(self, func):
        self._func = func
        self._cache = {}
    def __call__(self, *args, **kw):
        key = dumps((args, kw.items()), -1)
        if key not in self._cache:
            self._cache[key] = self._func(*args, **kw)
        return self._cache[key]

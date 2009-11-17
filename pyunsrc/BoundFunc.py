class BoundFunc(object):
    def __init__(self, func, *args, **kw):
        self.func, self.args, self.kw = func, args, kw
    def __call__(self, *new_args, **new_kw):
        new_kw.update(self.kw)
        return self.func(*(self.args + new_args), **new_kw)

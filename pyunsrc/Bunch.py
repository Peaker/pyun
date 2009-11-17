class Bunch(object):
    def __init__(self, **kw):
        self.__dict__['_Bunch_kw'] = kw
    def __getattr__(self, name):
        try:
            return self._Bunch_kw[name]
        except KeyError, e:
            raise AttributeError, e
    def __setattr__(self, name, value):
        self._Bunch_kw[name] = value
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(['%s=%r' % item
                                      for item in self._Bunch_kw.items()]))
    def __iter__(self):
        return iter(self._Bunch_kw)

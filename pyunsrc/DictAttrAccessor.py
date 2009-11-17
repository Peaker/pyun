class DictAttrAccessor(object):
    def __init__(self, some_dict):
        self.__dict__['_DictAttrAccessor_some_dict'] = some_dict
    def __getattr__(self, name):
        try:
            return self._DictAttrAccessor_some_dict[name]
        except KeyError, e:
            raise AttributeError, e
    def __setattr__(self, name, value):
        self._DictAttrAccessor_some_dict[name] = value
    def __iter__(self):
        return iter(self._DictAttrAccessor_some_dict)

def dict(x):
    return x._DictAttrAccessor_some_dict

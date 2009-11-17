class ADict(dict):
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        return self[name]
    def __delattr__(self, name):
        del self[name]

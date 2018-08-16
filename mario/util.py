import collections
from itertools import chain

class ElasticDict(collections.MutableMapping):
    def __init__(self, d={}):
        self.original = d
        self.strain = {}

    def __setitem__(self, i, x):
        self.strain[i] = x

    def __getitem__(self, i):
        try:
            return self.strain[i]
        except KeyError:
            return self.original[i]

    def __delitem__(self, key):
        del self.strain[key]

    def __iter__(self):
        return iter(set(self.original) | set(self.strain))

    def __len__(self):
        return len(set(self.original.keys()) | set(self.strain.keys()))

    def __str__(self):
        t = self.original.copy()
        t.update(self.strain)
        return str(t)

    def __repr__(self):
        return str(self)

    def reverse(self):
        self.strain.clear()

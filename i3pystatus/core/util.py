
import collections
import itertools

from .exceptions import *
from .imputil import ClassFinder

def lchop(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix):]
    return string

def popwhile(predicate, iterable):
    while iterable:
        item = iterable.pop()
        if predicate(item):
            yield item
        else:
            break

def partition(iterable, limit, key=lambda x: x):
    def pop_partition():
        sum = 0.0
        while sum < limit and iterable:
            sum += key(iterable[-1])
            yield iterable.pop()

    partitions = []
    iterable.sort(reverse=True)
    while iterable:
        partitions.append(list(pop_partition()))

    return partitions

def round_dict(dic, places):
    for key, value in dic.items():
        dic[key] = round(value, places)

class ModuleList(collections.UserList):
    def __init__(self, status_handler, module_base):
        self.status_handler = status_handler
        self.finder = ClassFinder(module_base)
        super().__init__()

    def append(self, module, *args, **kwargs):
        module = self.finder.instanciate_class_from_module(module, *args, **kwargs)
        module.registered(self.status_handler)
        super().append(module)
        return module

    def get_by_id(self, find_id):
        find_id = int(find_id)
        for module in self:
            if int(id(module)) == find_id:
                return module
        return None

class PrefixedKeyDict(collections.UserDict):
    def __init__(self, prefix):
        super().__init__()

        self.prefix = prefix

    def __setitem__(self, key, value):
        super().__setitem__(self.prefix + key, value)

class KeyConstraintDict(collections.UserDict):
    class MissingKeys(Exception):
        def __init__(self, keys):
            self.keys = keys

    def __init__(self, valid_keys, required_keys):
        super().__init__()

        self.valid_keys = valid_keys
        self.required_keys = set(required_keys)
        self.seen_keys = set()

    def __setitem__(self, key, value):
        if key in self.valid_keys:
            self.seen_keys.add(key)
            self.data[key] = value
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        self.seen_keys.remove(key)
        del self.data[key]

    def __iter__(self):
        if self.missing():
            raise self.MissingKeys(self.missing())

        return self.data.__iter__()

    def missing(self):
        return self.required_keys - (self.seen_keys & self.required_keys)

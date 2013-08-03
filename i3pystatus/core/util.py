
import collections
import itertools
import re

from .exceptions import *
from .imputil import ClassFinder

def chain(fun):
    def chained(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        return self
    return chained

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

def convert_position(pos, json):
    if pos < 0:
        pos = len(json) + (pos+1)
    return pos

def formatp(string, **kwargs):
    """
    Function for advanced format strings with partial formatting

    This function consumes format strings with groups enclosed in brackets. A
    group enclosed in brackets will only become part of the result if all fields
    inside the group evaluate True in boolean contexts.

    Groups can be nested. The fields in a nested group do not count as fields in
    the enclosing group, i.e. the enclosing group will evaluate to an empty
    string even if a nested group would be eligible for formatting. Nesting is
    thus equivalent to a logical or of all enclosing groups with the enclosed
    group.

    Escaped brackets, i.e. \[ and \] are copied verbatim to output.
    """

    pbracket = formatp.obracket_re.search(string)
    if not pbracket:
        return string.format(**kwargs)
    pbracket = pbracket.start()
    sbracket = list(formatp.cbracket_re.finditer(string))[-1].end()-1

    prefix = string[:pbracket].format(**kwargs)
    suffix = string[sbracket+1:].format(**kwargs)
    string = string[pbracket+1:sbracket]

    while True:
        b = formatp.obracket_re.search(string)
        e = list(formatp.cbracket_re.finditer(string))
        if b and e:
            b = b.start()
            e = e[-1].end()
            string = string[:b] + formatp(string[b:e], **kwargs) + string[e:]
        else:
            break

    fields = formatp.field_re.findall(string)
    successful_fields = 0
    for fieldspec, fieldname in fields:
        if kwargs.get(fieldname, False):
            successful_fields += 1

    if successful_fields != len(fields):
        return prefix + suffix
    else:
        string = string.replace("\[", "[").replace("\]", "]")
        return prefix + string.format(**kwargs) + suffix

formatp.field_re = re.compile(r"({(\w+)[^}]*})")
formatp.obracket_re = re.compile(r"(?<!\\)\[")
formatp.cbracket_re = re.compile(r"(?<!\\)\]")

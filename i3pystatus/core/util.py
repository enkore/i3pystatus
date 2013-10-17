
import collections
import functools
import itertools
import re
import socket
import string

from i3pystatus.core.exceptions import *
from i3pystatus.core.imputil import ClassFinder


def chain(fun):
    def chained(self, *args, **kwargs):
        fun(self, *args, **kwargs)
        return self
    return chained


def lchop(string, prefix):
    """Removes a prefix from string

    :param string: String, possibly prefixed with prefix
    :param prefix: Prefix to remove from string
    :returns: string without the prefix
    """
    if string.startswith(prefix):
        return string[len(prefix):]
    return string


def popwhile(predicate, iterable):
    """Generator function yielding items of iterable while predicate holds for each item

    :param predicate: function taking an item returning bool
    :param iterable: iterable
    :returns: iterable (generator function)
    """
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
    """
    Rounds all values in a dict containing only numeric types to `places` decimal places.
    """
    for key, value in dic.items():
        dic[key] = round(value, places)


class ModuleList(collections.UserList):
    def __init__(self, status_handler, module_base):
        self.status_handler = status_handler
        self.finder = ClassFinder(module_base)
        super().__init__()

    def append(self, module, *args, **kwargs):
        module = self.finder.instanciate_class_from_module(
            module, *args, **kwargs)
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
    """
    A dict implementation adding a prefix to every key added

    :param prefix: Prefix to prepend
    """

    def __init__(self, prefix):
        super().__init__()

        self.prefix = prefix

    def __setitem__(self, key, value):
        super().__setitem__(self.prefix + key, value)


class KeyConstraintDict(collections.UserDict):
    """
    A dict implementation with sets of valid and required keys

    :param valid_keys: Set of valid keys
    :param required_keys: Set of required keys, must be a subset of valid_keys
    """

    class MissingKeys(Exception):
        def __init__(self, keys):
            self.keys = keys

    def __init__(self, valid_keys, required_keys):
        super().__init__()

        self.valid_keys = valid_keys
        self.required_keys = set(required_keys)
        self.seen_keys = set()

    def __setitem__(self, key, value):
        """Trying to add an invalid key will raise KeyError
        """
        if key in self.valid_keys:
            self.seen_keys.add(key)
            self.data[key] = value
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        self.seen_keys.remove(key)
        del self.data[key]

    def __iter__(self):
        """Iteration will raise a MissingKeys exception unless all required keys are set
        """
        if self.missing():
            raise self.MissingKeys(self.missing())

        return self.data.__iter__()

    def missing(self):
        """Returns a set of keys that are required but not set
        """
        return self.required_keys - (self.seen_keys & self.required_keys)


def convert_position(pos, json):
    if pos < 0:
        pos = len(json) + (pos + 1)
    return pos


def flatten(l):
    """
    Flattens a hierarchy of nested lists into a single list containing all elements in order

    :param l: list of arbitrary types and lists
    :returns: list of arbitrary types
    """
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], list):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return l


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

    Escaped brackets, i.e. \\[ and \\] are copied verbatim to output.

    :param string: Format string
    :param **kwargs: keyword arguments providing data for the format string
    :returns: Formatted string
    """

    def build_stack(string):
        """
        Builds a stack with OpeningBracket, ClosingBracket and String tokens.
        Tokens have a level property denoting their nesting level.
        They also have a string property containing associated text (empty for
        all tokens but String tokens).
        """
        class Token:
            string = ""

            def __repr__(self):
                return "<%s> " % self.__class__.__name__

        class OpeningBracket(Token):
            def __repr__(self):
                return "<Group>"

        class ClosingBracket(Token):
            def __repr__(self):
                return "</Group>"

        class String(Token):
            def __init__(self, str):
                self.string = str

            def __repr__(self):
                return super().__repr__() + repr(self.string)

        TOKENS = {
            "[": OpeningBracket,
            "]": ClosingBracket,
        }

        stack = []

        # Index of next unconsumed char
        next = 0
        # Last consumed char
        prev = ""
        # Current char
        char = ""
        # Current level
        level = 0

        while next < len(string):
            prev = char
            char = string[next]
            next += 1

            if prev != "\\" and char in TOKENS:
                token = TOKENS[char]()
                token.index = next
                if char == "]":
                    level -= 1
                token.level = level
                if char == "[":
                    level += 1
                stack.append(token)
            else:
                if stack and isinstance(stack[-1], String):
                    stack[-1].string += char
                else:
                    token = String(char)
                    token.level = level
                    stack.append(token)
        return stack

    def build_tree(items, level=0):
        """
        Builds a list-of-lists tree (in forward order) from a stack (reversed order),
        and formats the elements on the fly, discarding everything not eligible for
        inclusion.
        """
        subtree = []

        while items:
            nested = []
            while items[0].level > level:
                nested.append(items.pop(0))
            if nested:
                subtree.append(build_tree(nested, level + 1))

            item = items.pop(0)
            if item.string:
                string = item.string
                if level == 0:
                    subtree.append(string.format(**kwargs))
                else:
                    fields = re.findall(r"({(\w+)[^}]*})", string)
                    successful_fields = 0
                    for fieldspec, fieldname in fields:
                        if kwargs.get(fieldname, False):
                            successful_fields += 1
                    if successful_fields == len(fields):
                        subtree.append(string.format(**kwargs))
                    else:
                        return []
        return subtree

    def merge_tree(items):
        return "".join(flatten(items)).replace("\]", "]").replace("\[", "[")

    stack = build_stack(string)
    tree = build_tree(stack, 0)
    return merge_tree(tree)


class TimeWrapper:
    """
    A wrapper that implements __format__ and __bool__ for time differences and time spans.

    :param seconds: seconds (numeric)
    :param default_format: the default format to be used if no explicit format_spec is passed to __format__

    Format string syntax:

    * %h, %m and %s are the hours, minutes and seconds without leading zeros (i.e. 0 to 59 for minutes and seconds)
    * %H, %M and %S are padded with a leading zero to two digits, i.e. 00 to 59
    * %l and %L produce hours non-padded and padded but only if hours is not zero. If the hours are zero it produces an empty string.
    * %% produces a literal %
    * %E (only valid on beginning of the string) if the time is null, don't format anything but rather produce an empty string. If the time is non-null it is removed from the string.

    The formatted string is stripped, i.e. spaces on both ends of the result are removed
    """

    class TimeTemplate(string.Template):
        delimiter = "%"
        idpattern = r"[a-zA-Z]"

    def __init__(self, seconds, default_format="%m:%S"):
        self.seconds = int(seconds)
        self.default_format = default_format

    def __bool__(self):
        """:returns: `bool(seconds)`, i.e. False if seconds == 0 and True otherwise
        """
        return bool(self.seconds)

    def __format__(self, format_spec):
        """Formats the time span given the format_spec (or the default_format).
        """
        format_spec = format_spec or self.default_format
        h = self.seconds // 3600
        m, s = divmod(self.seconds % 3600, 60)
        l = h if h else ""
        L = "%02d" % h if h else ""

        if format_spec.startswith("%E"):
            format_spec = format_spec[2:]
            if not self.seconds:
                return ""
        return self.TimeTemplate(format_spec).substitute(
            h=h, m=m, s=s,
            H="%02d" % h, M="%02d" % m, S="%02d" % s,
            l=l, L=L,
        ).strip()


def render_json(json):
    if not json.get("full_text", ""):
        return ""

    return json["full_text"]


def require(predicate):
    """
    Decorator factory for methods requiring a predicate. If the predicate is not fulfilled during a method call, the
    method call is skipped and None is returned.

    :param predicate: A callable returning a truth value
    :returns: Method decorator

    .. seealso::

        :py:func:`internet`
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            if predicate():
                return method(*args, **kwargs)
            return None
        return wrapper
    return decorator


def internet():
    """
    Checks for a internet connection by connecting to 8.8.8.8 (Google DNS)

    :returns: True if internet connection is available
    """
    try:
        socket.create_connection(("8.8.8.8", 53), 1).close()
        return True
    except OSError:
        return False

import collections
import functools
import re
import socket
import string
import inspect
from threading import Timer, RLock

import time


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
    If places is None, round to INT.
    """
    if places is None:
        for key, value in dic.items():
            dic[key] = round(value)
    else:
        for key, value in dic.items():
            dic[key] = round(value, places)


class ModuleList(collections.UserList):
    def __init__(self, status_handler, class_finder):
        self.status_handler = status_handler
        self.finder = class_finder
        super().__init__()

    def append(self, module, *args, **kwargs):
        module = self.finder.instanciate_class_from_module(
            module, *args, **kwargs)
        module.registered(self.status_handler)
        super().append(module)
        return module

    def get(self, find_id):
        find_id = int(find_id)
        for module in self:
            if id(module) == find_id:
                return module


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


def bytes_info_dict(in_bytes):
    power = 2**10  # 2 ** 10 == 1024
    n = 0
    pow_dict = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    out_bytes = int(in_bytes)
    while out_bytes > power:
        out_bytes /= power
        n += 1
    return {
        'value': out_bytes,
        'unit': '{prefix}B'.format(prefix=pow_dict[n])
    }


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

    Escaped brackets, i.e. \\\\[ and \\\\] are copied verbatim to output.

    :param string: Format string
    :param kwargs: keyword arguments providing data for the format string
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

        class OpeningBracket(Token):
            pass

        class ClosingBracket(Token):
            pass

        class String(Token):
            def __init__(self, str):
                self.string = str

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
        return "".join(flatten(items)).replace(r"\]", "]").replace(r"\[", "[")

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


def require(predicate):
    """Decorator factory for methods requiring a predicate. If the
    predicate is not fulfilled during a method call, the method call
    is skipped and None is returned.

    :param predicate: A callable returning a truth value
    :returns: Method decorator

    .. seealso::

        :py:class:`internet`

    """

    def decorator(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            if predicate():
                return method(*args, **kwargs)
            return None

        return wrapper

    return decorator


class internet:
    """
    Checks for internet connection by connecting to a server.

    This class exposes two configuration variables:
        * address - a tuple containing (host,port) of the server to connect to
        * check_frequency - the frequency in seconds for checking the connection

    :rtype: bool

    .. seealso::

        :py:func:`require`

    """
    address = ('google.com', 80)
    check_frequency = 1

    dns_cache = []
    last_checked = time.perf_counter() - check_frequency

    connected = False

    def __new__(cls):
        if not internet.connected:
            internet.dns_cache = internet.resolve()

        now = time.perf_counter()
        elapsed = now - internet.last_checked
        if not internet.connected or elapsed > internet.check_frequency:
            internet.last_checked = now
            internet.connected = internet.check_connection()
        return internet.connected

    @staticmethod
    def check_connection():
        for res in internet.dns_cache:
            try:
                if internet.check(res):
                    return True
            except OSError:
                pass
        return False

    @staticmethod
    def check(res):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)
            sock.settimeout(1)
            sock.connect(sa)
            sock.close()
            return True
        except socket.error:
            if sock is not None:
                sock.close()
            raise

    @staticmethod
    def resolve():
        host, port = internet.address
        try:
            return socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        except socket.gaierror:
            return []


def make_graph(values, lower_limit=0.0, upper_limit=100.0, style="blocks"):
    """
    Draws a graph made of unicode characters.

    :param values: An array of values to graph.
    :param lower_limit: Minimum value for the y axis (or None for dynamic).
    :param upper_limit: Maximum value for the y axis (or None for dynamic).
    :param style: Drawing style ('blocks', 'braille-fill', 'braille-peak', or 'braille-snake').
    :returns: Bar as a string
    """

    values = [float(n) for n in values]
    mn, mx = min(values), max(values)
    mn = mn if lower_limit is None else min(mn, float(lower_limit))
    mx = mx if upper_limit is None else max(mx, float(upper_limit))
    extent = mx - mn

    if style == 'blocks':
        bar = '_▁▂▃▄▅▆▇█'
        bar_count = len(bar) - 1
        if extent == 0:
            graph = '_' * len(values)
        else:
            graph = ''.join(bar[int((n - mn) / extent * bar_count)] for n in values)
    elif style in ['braille-fill', 'braille-peak', 'braille-snake']:
        # idea from https://github.com/asciimoo/drawille
        # unicode values from http://en.wikipedia.org/wiki/Braille

        vpad = values if len(values) % 2 == 0 else values + [mn]
        vscale = [round(4 * (vp - mn) / extent) for vp in vpad]
        l = len(vscale) // 2

        # do the 2-character collapse separately for clarity
        if 'fill' in style:
            vbits = [[0, 0x40, 0x44, 0x46, 0x47][vs] for vs in vscale]
        elif 'peak' in style:
            vbits = [[0, 0x40, 0x04, 0x02, 0x01][vs] for vs in vscale]
        else:
            assert('snake' in style)
            # there are a few choices for what to put last in vb2.
            # arguable vscale[-1] from the _previous_ call is best.
            vb2 = [vscale[0]] + vscale + [0]
            vbits = []
            for i in range(1, l + 1):
                c = 0
                for j in range(min(vb2[i - 1], vb2[i], vb2[i + 1]), vb2[i] + 1):
                    c |= [0, 0x40, 0x04, 0x02, 0x01][j]
                vbits.append(c)

        # 2-character collapse
        graph = ''
        for i in range(0, l, 2):
            b1 = vbits[i]
            b2 = vbits[i + 1]
            if b2 & 0x40:
                b2 = b2 - 0x30
            b2 = b2 << 3
            graph += chr(0x2800 + b1 + b2)
    else:
        raise NotImplementedError("Graph drawing style '%s' unimplemented." % style)
    return graph


def make_vertical_bar(percentage, width=1, glyphs=None):
    """
    Draws a vertical bar made of unicode characters.

    :param percentage: A value between 0 and 100
    :param width: How many characters wide the bar should be.
    :returns: Bar as a String
    """
    if glyphs is not None:
        bar = make_glyph(percentage, lower_bound=0, upper_bound=100, glyphs=glyphs)
    else:
        bar = make_glyph(percentage, lower_bound=0, upper_bound=100)
    return bar * width


def make_bar(percentage):
    """
    Draws a bar made of unicode box characters.

    :param percentage: A value between 0 and 100
    :returns: Bar as a string
    """

    bars = [' ', '▏', '▎', '▍', '▌', '▋', '▋', '▊', '▊', '█']
    tens = int(percentage / 10)
    ones = int(percentage) - tens * 10
    result = tens * '█'
    if ones >= 1:
        result = result + bars[ones]
    result = result + (10 - len(result)) * ' '
    return result


def make_glyph(number, glyphs=" _▁▂▃▄▅▆▇█", lower_bound=0, upper_bound=100, enable_boundary_glyphs=False):
    """
    Returns a single glyph from the list of glyphs provided relative to where
    the number is in the range (by default a percentage value is expected).

    This can be used to create an icon based representation of a value with an
    arbitrary number of glyphs (e.g. 4 different battery status glyphs for
    battery percentage level).

    :param number: The number being represented.  By default a percentage value\
    between 0 and 100 (but any range can be defined with lower_bound and\
    upper_bound).
    :param glyphs: Either a string of glyphs, or an array of strings.  Using an array\
    of strings allows for additional pango formatting to be applied such that\
    different colors could be shown for each glyph).
    :param lower_bound:  A custom lower bound value for the range.
    :param upper_bound:  A custom upper bound value for the range.
    :param enable_boundary_glyphs: Whether the first and last glyphs should be used\
    for the special case of the number being <= lower_bound or >= upper_bound\
    respectively.
    :returns: The glyph found to represent the number
    """

    # Handle edge cases first
    if lower_bound >= upper_bound:
        raise Exception("Invalid upper/lower bounds")
    elif number <= lower_bound:
        return glyphs[0]
    elif number >= upper_bound:
        return glyphs[-1]

    if enable_boundary_glyphs:
        # Trim first and last items from glyphs as boundary conditions already
        # handled
        glyphs = glyphs[1:-1]

    # Determine a value 0 - 1 that represents the position in the range
    adjusted_value = (number - lower_bound) / (upper_bound - lower_bound)

    # Determine the closest glyph to show
    # As we have positive indices, we can use int for floor rounding
    # Adjusted_value should always be < 1
    glyph_index = int(len(glyphs) * adjusted_value)

    return glyphs[glyph_index]


def user_open(url_or_command):
    """Open the specified paramater in the web browser if a URL is detected,
    othewrise pass the paramater to the shell as a subprocess. This function
    is inteded to bu used in on_leftclick/on_rightclick callbacks.

    :param url_or_command: String containing URL or command
    """
    from urllib.parse import urlparse
    scheme = urlparse(url_or_command).scheme
    if scheme == 'http' or scheme == 'https':
        import webbrowser
        import os
        # webbrowser.open() sometimes prints a message for some reason and confuses i3
        # Redirect stdout briefly to prevent this from happening.
        savout = os.dup(1)
        os.close(1)
        os.open(os.devnull, os.O_RDWR)
        try:
            webbrowser.open(url_or_command)
        finally:
            os.dup2(savout, 1)
    else:
        import subprocess
        subprocess.Popen(url_or_command, shell=True)


class MultiClickHandler(object):
    def __init__(self, callback_handler, timeout):
        self.callback_handler = callback_handler
        self.timeout = timeout

        self.lock = RLock()

        self._timer_id = 0
        self.timer = None
        self.button = None
        self.cb = None
        self.kwargs = None

    def set_timer(self, button, cb, **kwargs):
        with self.lock:
            self.clear_timer()

            self.timer = Timer(self.timeout,
                               self._timer_function,
                               args=[self._timer_id])
            self.button = button
            self.cb = cb
            self.kwargs = kwargs

            self.timer.start()

    def clear_timer(self):
        with self.lock:
            if self.timer is None:
                return

            self._timer_id += 1  # Invalidate existent timer

            self.timer.cancel()  # Cancel the existent timer

            self.timer = None
            self.button = None
            self.cb = None

    def _timer_function(self, timer_id):
        with self.lock:
            if self._timer_id != timer_id:
                return
            self.callback_handler(self.button, self.cb, **self.kwargs)
            self.clear_timer()

    def check_double(self, button):
        if self.timer is None:
            return False

        ret = True
        if button != self.button:
            self.callback_handler(self.button, self.cb, **self.kwargs)
            ret = False

        self.clear_timer()
        return ret


def get_module(function):
    """Function decorator for retrieving the ``self`` argument from the stack.

    Intended for use with callbacks that need access to a modules variables, for example:

    .. code:: python

        from i3pystatus import Status, get_module
        from i3pystatus.core.command import execute
        status = Status(...)
        # other modules etc.
        @get_module
        def display_ip_verbose(module):
            execute('sh -c "ip addr show dev {dev} | xmessage -file -"'.format(dev=module.interface))
        status.register("network", interface="wlan1", on_leftclick=display_ip_verbose)
    """
    @functools.wraps(function)
    def call_wrapper(*args, **kwargs):
        stack = inspect.stack()
        caller_frame_info = stack[1]
        self = caller_frame_info[0].f_locals["self"]
        # not completly sure whether this is necessary
        # see note in Python docs about stack frames
        del stack
        function(self, *args, **kwargs)
    return call_wrapper

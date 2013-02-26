
import inspect
import types
import collections
from threading import Thread
import time

from .exceptions import *

__all__ = [
    "SettingsBase",
    "ClassFinder",
    "ModuleList",
    "KeyConstraintDict", "PrefixedKeyDict",
    "WorkerPool", "IntervalWorkerPool",
]

class ModuleList(collections.UserList):
    def __init__(self, status_handler, module_base):
        self.status_handler = status_handler
        self.finder = ClassFinder(module_base)
        super().__init__()

    def append(self, module, *args, **kwargs):
        module = self.finder.instanciate_class_from_module(module, *args, **kwargs)
        module.registered(self.status_handler)
        super().append(module)

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

    def __iter__(self):
        if self.missing():
            raise self.MissingKeys(self.missing())

        return self.data.__iter__()

    def missing(self):
        return self.required_keys - (self.seen_keys & self.required_keys)

class SettingsBase:
    """
    Support class for providing a nice and flexible settings interface

    Classes inherit from this class and define what settings they provide and
    which are required.

    The constructor is either passed a dictionary containing these settings, or
    keyword arguments specifying the same.

    Settings are stored as attributes of self
    """

    settings = tuple()
    """settings should be tuple containing two types of elements:
    * bare strings, which must be valid identifiers.
    * two-tuples, the first element being a identifier (as above) and the second
    a docstring for the particular setting"""

    required = tuple()
    """required can list settings which are required"""

    def __init__(self, *args, **kwargs):
        def flatten_setting(setting):
            return setting[0] if isinstance(setting, tuple) else setting
        def flatten_settings(settings):
            return tuple(flatten_setting(setting) for setting in settings)

        def get_argument_dict(args, kwargs):
            if len(args) == 1 and not kwargs:
                # User can also pass in a dict for their settings
                # Note: you could do that anyway, with the ** syntax
                return args[0]
            return kwargs

        self.settings = flatten_settings(self.settings)

        sm = KeyConstraintDict(self.settings, self.required)
        settings_source = get_argument_dict(args, kwargs)

        try:
            sm.update(settings_source)
        except KeyError as exc:
           raise ConfigKeyError(type(self).__name__, key=exc.args[0]) from exc

        try:
            self.__dict__.update(sm)
        except KeyConstraintDict.MissingKeys as exc:
            raise ConfigMissingError(type(self).__name__, missing=exc.keys) from exc

        self.__name__ = "{}.{}".format(self.__module__, self.__class__.__name__)

        self.init()

    def init(self):
        """Convenience method which is called after all settings are set

        In case you don't want to type that super()…blabla :-)"""

class ClassFinder:
    """Support class to find classes of specific bases in a module"""

    def __init__(self, baseclass):
        self.baseclass = baseclass

    def predicate_factory(self, module):
        def predicate(obj):
            return (
                inspect.isclass(obj) and
                issubclass(obj, self.baseclass) and
                obj.__module__ == module.__name__
            )
        return predicate

    def search_module(self, module):
        return list(zip(*inspect.getmembers(module, self.predicate_factory(module))))[1]

    def get_class(self, module):
        classes = self.search_module(module)

        if len(classes) > 1:
            # If there are multiple Module clases bundled in one module,
            # well, we can't decide for the user.
            raise ConfigAmbigiousClassesError(module.__name__, classes)
        elif not classes:
            raise ConfigInvalidModuleError(module.__name__)

        return classes[0]

    def get_module(self, module):
        return getattr(__import__("i3pystatus.{module}".format(module=module), globals(), {}, []), module)

    def instanciate_class_from_module(self, module, *args, **kwargs):
        if isinstance(module, types.ModuleType):
            return self.get_class(module)(*args, **kwargs)
        elif isinstance(module, str):
            return self.instanciate_class_from_module(self.get_module(module), *args, **kwargs)
        elif args or kwargs:
            raise ValueError("Additional arguments are invalid if 'module' is already an object")
        return module

class WorkerPool:
    def __init__(self):
        self.items = []

    def __call__(self):
        for item in self.items:
            item()

    def start(self):
        self.thread = Thread(target=self)
        self.thread.daemon = True
        self.thread.start()

class IntervalWorkerPool(WorkerPool):
    def __init__(self, interval):
        super().__init__()
        self.interval = interval

    def __call__(self):
        super().__call__()
        time.sleep(self.interval)

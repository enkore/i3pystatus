
import inspect
import types
import collections

from .exceptions import *

__all__ = [
    "SettingsBase",
    "ClassFinder",
]

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

    def missing(self):
        return self.required_keys - (self.seen_keys & self.required_keys)

    def __iter__(self):
        if self.missing():
            raise self.MissingKeys(self.missing())

        return self.data.__iter__()

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
        # Neat trick: [(x,y),(u,v)] becomes [(x,u),(y,v)]
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

    def instanciate_class_from_module(self, module, *args, **kwargs):
        if isinstance(module, types.ModuleType):
            return self.get_class(module)(*args, **kwargs)
        elif args or kwargs:
            raise ValueError("Additional arguments are invalid if 'module' is already an object")
        return module

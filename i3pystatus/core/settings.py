from .util import KeyConstraintDict
from .exceptions import ConfigKeyError, ConfigMissingError

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

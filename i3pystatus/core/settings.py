from i3pystatus.core.util import KeyConstraintDict
from i3pystatus.core.exceptions import ConfigKeyError, ConfigMissingError
import inspect


class SettingsBase:

    """
    Support class for providing a nice and flexible settings interface

    Classes inherit from this class and define what settings they provide and
    which are required.

    The constructor is either passed a dictionary containing these settings, or
    keyword arguments specifying the same.

    Settings are stored as attributes of self.
    """

    settings = (
        ("enable_log", "Set to true to log error to .i3pystatus-<pid> file"),
    )

    """settings should be tuple containing two types of elements:

    * bare strings, which must be valid Python identifiers.
    * two-tuples, the first element being a identifier (as above)
    and the second a docstring for the particular setting"""

    required = tuple()
    """required can list settings which are required"""

    enable_log = False

    def __init__(self, *args, **kwargs):
        def get_argument_dict(args, kwargs):
            if len(args) == 1 and not kwargs:
                # User can also pass in a dict for their settings
                # Note: you could do that anyway, with the ** syntax
                return args[0]
            return kwargs

        def merge_with_parents_settings():

            settings = tuple()

            # getmro returns base classes according to Method Resolution Order
            for cls in inspect.getmro(self.__class__):
                if hasattr(cls, "settings"):
                    settings = settings + cls.settings
            return settings

        settings = merge_with_parents_settings()
        settings = self.flatten_settings(settings)

        sm = KeyConstraintDict(settings, self.required)
        settings_source = get_argument_dict(args, kwargs)

        try:
            sm.update(settings_source)
        except KeyError as exc:
            raise ConfigKeyError(type(self).__name__, key=exc.args[0]) from exc

        try:
            self.__dict__.update(sm)
        except KeyConstraintDict.MissingKeys as exc:
            raise ConfigMissingError(
                type(self).__name__, missing=exc.keys) from exc

        self.__name__ = "{}.{}".format(
            self.__module__, self.__class__.__name__)

        self.init()

    def init(self):
        """Convenience method which is called after all settings are set

        In case you don't want to type that super()…blabla :-)"""

    @staticmethod
    def flatten_settings(settings):
        def flatten_setting(setting):
            return setting[0] if isinstance(setting, tuple) else setting

        return tuple(flatten_setting(setting) for setting in settings)

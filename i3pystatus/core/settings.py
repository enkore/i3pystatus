from i3pystatus.core.util import KeyConstraintDict
from i3pystatus.core.exceptions import ConfigKeyError, ConfigMissingError
import inspect
import logging
import getpass


class SettingsBaseMeta(type):
    """Add interval setting to `settings` attribute if it does not exist."""

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        cls.settings, cls.required = SettingsBaseMeta.get_merged_settings(cls)

    @staticmethod
    def get_merged_settings(cls):
        def unique(settings):
            def name(s):
                return s[0] if isinstance(s, tuple) else s
            seen = set()
            return [setting for setting in settings if not (
                name(setting) in seen or seen.add(name(setting)))]

        settings = tuple()
        required = set()
        # getmro returns base classes according to Method Resolution Order,
        # which always includes the class itself as the first element.
        for base in inspect.getmro(cls):
            settings += tuple(getattr(base, "settings", []))
            required |= set(getattr(base, "required", []))
        # if a derived class defines a default for a setting it is not
        # required anymore, provided that default is not set to None.
        for base in inspect.getmro(cls):
            for r in list(required):
                if hasattr(base, r) and getattr(base, r) != getattr(cls, r) \
                        or hasattr(cls, r) and getattr(cls, r) is not None:
                    required.remove(r)

        return unique(settings), required


class SettingsBase(metaclass=SettingsBaseMeta):
    """
    Support class for providing a nice and flexible settings interface

    Classes inherit from this class and define what settings they provide and
    which are required.

    The constructor is either passed a dictionary containing these settings, or
    keyword arguments specifying the same.

    Settings are stored as attributes of self.
    """

    __PROTECTED_SETTINGS = ["password", "email", "username"]

    settings = (
        ("log_level", "Set to true to log error to .i3pystatus-<pid> file."),
    )

    """settings should be tuple containing two types of elements:

    * bare strings, which must be valid Python identifiers.
    * two-tuples, the first element being a identifier (as above) and the second a docstring for the particular setting

    """

    required = tuple()
    """required can list settings which are required"""

    log_level = logging.WARNING
    logger = None

    def __init__(self, *args, **kwargs):
        def get_argument_dict(args, kwargs):
            if len(args) == 1 and not kwargs:
                # User can also pass in a dict for their settings
                # Note: you could do that anyway, with the ** syntax
                return args[0]
            return kwargs

        self.__name__ = "{}.{}".format(self.__module__, self.__class__.__name__)

        settings = self.flatten_settings(self.settings)

        sm = KeyConstraintDict(settings, self.required)
        settings_source = get_argument_dict(args, kwargs)

        protected = self.get_protected_settings(settings_source)
        settings_source.update(protected)

        try:
            sm.update(settings_source)
        except KeyError as exc:
            raise ConfigKeyError(type(self).__name__, key=exc.args[0]) from exc

        try:
            self.__dict__.update(sm)
        except KeyConstraintDict.MissingKeys as exc:
            raise ConfigMissingError(
                type(self).__name__, missing=exc.keys) from exc

        if self.__name__.startswith("i3pystatus"):
            self.logger = logging.getLogger(self.__name__)
        else:
            self.logger = logging.getLogger("i3pystatus." + self.__name__)
        self.logger.setLevel(self.log_level)
        self.init()

    def get_protected_settings(self, settings_source):
        """
        Attempt to retrieve protected settings from keyring if they are not already set.
        """
        user_backend = settings_source.get('keyring_backend')
        found_settings = dict()
        for setting_name in self.__PROTECTED_SETTINGS:
                # Nothing to do if the setting is already defined.
                if settings_source.get(setting_name):
                    continue

                setting = None
                identifier = "%s.%s" % (self.__name__, setting_name)
                if hasattr(self, 'required') and setting_name in getattr(self, 'required'):
                    setting = self.get_setting_from_keyring(identifier, user_backend)
                elif hasattr(self, setting_name):
                    setting = self.get_setting_from_keyring(identifier, user_backend)
                if setting:
                    found_settings.update({setting_name: setting})
        return found_settings

    def get_setting_from_keyring(self, setting_identifier, keyring_backend=None):
        """
        Retrieves a protected setting from keyring
        :param setting_identifier: must be in the format package.module.Class.setting
        """
        # If a custom keyring backend has been defined, use it.
        if keyring_backend:
            return keyring_backend.get_password(setting_identifier, getpass.getuser())

        # Otherwise try and use default keyring.
        try:
            import keyring
        except ImportError:
            pass
        else:
            return keyring.get_password(setting_identifier, getpass.getuser())

    def init(self):
        """Convenience method which is called after all settings are set

        In case you don't want to type that super()…blabla :-)"""

    @staticmethod
    def flatten_settings(settings):
        def flatten_setting(setting):
            return setting[0] if isinstance(setting, tuple) else setting

        return tuple(flatten_setting(setting) for setting in settings)

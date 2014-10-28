from i3pystatus.core.util import KeyConstraintDict
from i3pystatus.core.exceptions import ConfigKeyError, ConfigMissingError
import inspect

class SettingsBase(object):
    """
    Support class for providing a nice and flexible settings interface

    Classes inherit from this class and define what settings they provide and
    which are required.

    The constructor is either passed a dictionary containing these settings, or
    keyword arguments specifying the same.

    Settings are stored as attributes of self.
    """

    settings = tuple()
    """settings should be tuple containing two types of elements:

    * bare strings, which must be valid Python identifiers.
    * two-tuples, the first element being a identifier (as above) and the second
      a docstring for the particular setting"""

    required = tuple()
    """required can list settings which are required"""

    def __init__(self, *args, **kwargs):
        def get_argument_dict(args, kwargs):
            if len(args) == 1 and not kwargs:
                # User can also pass in a dict for their settings
                # Note: you could do that anyway, with the ** syntax
                return args[0]
            return kwargs
        #self.settings
        self.settings = self.flatten_settings()

        sm = KeyConstraintDict(self.settings, self.required)
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

    
    def flatten_settings(self):
            #type(self),self
        # print("self",self, self.__class__.__name__)
        # if not isinstance(object,self):
        # for cls in inspect.getmro():
        settings = []

        # print(self.getmro())
        # print()
        # print("BAses", self.__class__.__bases__ )
        # print("MRO:", )
        for cls in  inspect.getmro(self.__class__):
            # print("toto",cls)
            # print("toto", cls)
            # print("name", cls.__name__)
            if hasattr(cls,"settings"):
                # settings = settings + ( super(cls,self).settings, )
                settings = settings + list( cls.settings )
        # if hasattr(super(), "flatten_settings" ):
        # # if issubclass(type(self),SettingsBase) and not (type(self) == SettingsBase):
        #     print(super())
        #     settings = settings + ( super().flatten_settings(), )
            # settings = super().flatten_settings()

        # print("Settings after loop: \n", settings)
        def flatten_setting(setting):
            return setting[0] if isinstance(setting, tuple) else setting

        return tuple(flatten_setting(setting) for setting in settings)

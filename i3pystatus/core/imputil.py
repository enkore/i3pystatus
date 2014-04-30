import inspect
import types
from importlib import import_module
from i3pystatus.core.exceptions import ConfigAmbigiousClassesError, ConfigInvalidModuleError


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

    def get_matching_classes(self, module):
        # Transpose [ (name, list), ... ] to ( [name, ...], [list, ...] )
        classes = list(zip(*inspect.getmembers(module, self.predicate_factory(module))))
        return classes[1] if classes else []

    def get_class(self, module):
        classes = self.get_matching_classes(module)

        if len(classes) > 1:
            # If there are multiple Module clases bundled in one module,
            # well, we can't decide for the user.
            raise ConfigAmbigiousClassesError(module.__name__, classes)
        elif not classes:
            raise ConfigInvalidModuleError(module.__name__)

        return classes[0]

    def get_module(self, module):
        return import_module("i3pystatus.{mod}".format(mod=module))

    def instanciate_class_from_module(self, module, *args, **kwargs):
        if isinstance(module, types.ModuleType):
            return self.get_class(module)(*args, **kwargs)
        elif isinstance(module, str):
            return self.instanciate_class_from_module(self.get_module(module), *args, **kwargs)
        elif inspect.isclass(module) and issubclass(module, self.baseclass):
            return module(*args, **kwargs)
        elif args or kwargs:
            raise ValueError(
                "Additional arguments are invalid if 'module' is already an object")
        return module

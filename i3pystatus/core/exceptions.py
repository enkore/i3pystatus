class ConfigError(Exception):
    """ABC for configuration exceptions"""

    def __init__(self, module, *args, **kwargs):
        self.message = "Module '{0}': {1}".format(
            module, self.format(*args, **kwargs))

        super().__init__(self.message)

    def format(self, *args, **kwargs):
        return ""


class ConfigKeyError(ConfigError, KeyError):
    def format(self, key):
        return "invalid option '{0}'".format(key)


class ConfigMissingError(ConfigError):
    def format(self, missing):
        return "missing required options: {0}".format(missing)


class ConfigAmbigiousClassesError(ConfigError):
    def format(self, ambigious_classes):
        return "ambigious module specification, found multiple classes: {0}".format(ambigious_classes)


class ConfigInvalidModuleError(ConfigError):
    def format(self):
        return "no class found"

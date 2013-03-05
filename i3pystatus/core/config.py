
import os
import os.path
import runpy

SEARCHPATH = (
    "~/.i3pystatus.py",
    "~/.i3/i3pystatus.py",
    "~/.config/i3pystatus.py",
    "$XDG_CONFIG_HOME/i3pystatus.py",
    "/etc/i3pystatus.py",
    "/etc/xdg/i3pystatus.py",
    "$XDG_CONFIG_DIRS/i3pystatus.py",
)

class ConfigFinder:
    def __init__(self, searchpath=SEARCHPATH):
        self.searchpath = searchpath

    @staticmethod
    def expand(path):
        return os.path.expandvars(os.path.expanduser(path))

    @staticmethod
    def exists(path):
        return os.path.isfile(path)

    def get_config_path(self):
        failed = []
        for path in map(self.expand, self.searchpath):
            if self.exists(path):
                return failed, path
            else:
                failed.append(path)

        return failed, None

    def run_config(self):
        failed, path = self.get_config_path()
        if path:
            runpy.run_path(path, run_name="i3pystatus._config")
        else:
            raise ImportError("Didn't find a config module, tried\n * {mods}".format(mods="\n * ".join(failed)))

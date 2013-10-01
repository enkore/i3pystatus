
import os.path
import runpy
import sys
import contextlib

from i3pystatus.core.util import render_json

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

    def find_config_file(self):
        failed = []
        for path in map(self.expand, self.searchpath):
            if self.exists(path):
                return path
            else:
                failed.append(path)

        raise RuntimeError(
            "Didn't find a config file, tried\n * {mods}".format(mods="\n * ".join(failed)))


class Config:

    def __init__(self, config_file=None):
        self.finder = ConfigFinder()
        self.config_file = config_file or self.finder.find_config_file()

    def run(self):
        runpy.run_path(self.config_file, run_name="i3pystatus._config")

    def test(self):
        @contextlib.contextmanager
        def setup():
            import i3pystatus

            class TestStatus(i3pystatus.Status):

                def run(self):
                    self.modules.reverse()
                    self.call_start_hooks()
                    for module in self.modules:
                        sys.stdout.write(
                            "{module}: ".format(module=module.__name__))
                        sys.stdout.flush()
                        test = module.test()
                        if test is not True:
                            print("\n\t", test)
                            continue
                        module.run()
                        output = module.output or {"full_text": "(no output)"}
                        print(render_json(output))

            i3pystatus.Status = TestStatus
            yield
            i3pystatus.Status = i3pystatus.Status.__bases__[0]

        with setup():
            print(
                "Using configuration file {file}\n".format(file=self.config_file))
            self.run()

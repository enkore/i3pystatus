import re

from i3pystatus import IntervalModule

class Regex(IntervalModule):
    """
    Simple regex file watcher

    Settings:
    * flags — Python.re flags
    * regex — regular expression
    * file — file to search for regex matches
    * format — new-style format string used for output, default is "{0}"
    """

    flags = 0
    format = "{0}"
    settings = ("format", "regex", "file")
    required = ("regex", "file")

    def init(self):
        self.re = re.compile(self.regex, self.flags)

    def run(self):
        with open(self.file, "r") as f:
            match = self.re.search(f.read())
            self.output = self.output = {
                "full_text" : self.format.format(*match.groups()),
                "name" : "regex",
            }
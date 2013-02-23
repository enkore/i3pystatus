#!/usr/bin/env python

import sys
import io
import pkgutil
from collections import namedtuple

import i3pystatus

IGNORE = ("__main__", "mkdocs")
MODULE_FORMAT = """
### {name}

{doc}

{settings}\n"""

def trim(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

class Module:
    name = ""
    doc = ""

    def __init__(self, cls, neighbours, module_name, module):
        self.settings = []
        self.cls = cls

        if neighbours == 1:
            self.name = module_name
        else:
            self.name = "{module}.{cls}".format(module=module_name, cls=self.cls.__name__)

        if hasattr(self.cls, "__doc__"):
            self.doc = self.cls.__doc__
        elif hasattr(module, "__doc__"):
            self.doc = module.__doc__

        self.get_settings()

    def get_settings(self):
        for setting in self.cls.settings:
            self.settings.append(Setting(self, setting))

    def format_settings(self):
        return "\n".join(map(lambda setting: setting.format(), self.settings))

    def format(self):
        return MODULE_FORMAT.format(
            name=self.name,
            doc=trim(self.doc),
            settings=self.format_settings(),
        )

class Setting:
    name = ""
    doc = ""
    required = False
    default = None

    def __init__(self, mod, setting):
        if isinstance(setting, tuple):
            self.name = setting[0]
            self.doc = setting[1]
        else:
            self.name = setting

        if setting in mod.cls.required:
            self.required = True
        elif hasattr(mod.cls, self.name):
            self.default = getattr(mod.cls, self.name)

    def format(self):
        attrs = []
        if self.required:
            attrs.append("required")
        if self.default:
            attrs.append("default: {default}".format(default=self.default))

        formatted = "* {name} ".format(name=self.name)
        if self.doc or attrs:
            formatted += "— "
            if self.doc:
                formatted += self.doc
            if attrs:
                formatted += " ({attrs})".format(attrs=", ".join(attrs))

        return formatted

def get_modules():
    modules = []
    for finder, modname, ispkg in pkgutil.iter_modules(i3pystatus.get_path()):
        if modname not in IGNORE:
            modules.append(get_module(finder, modname))

    return modules

def get_module(finder, modname):
    fullname = "i3pystatus.{modname}".format(modname=modname)
    return (modname, finder.find_loader(fullname)[0].load_module(fullname))

def get_all():
    mods = []
    finder = i3pystatus.ModuleFinder()

    for name, module in get_modules():
        classes = finder.search_module(module)

        for cls in classes:
            mods.append(Module(cls, neighbours=len(classes), module_name=name, module=module))

    return sorted(mods, key=lambda module: module.name)

with open("template.md", "r") as template:
    moddoc = "".join(map(lambda module: module.format(), get_all()))    

    print(template.read().replace("!!module_doc!!", moddoc))

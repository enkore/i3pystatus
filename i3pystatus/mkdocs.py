#!/usr/bin/env python

import sys
import io
import pkgutil
from collections import namedtuple
import textwrap

import i3pystatus
import i3pystatus.mail

from .core.util import ClassFinder

IGNORE = ("__main__", "mkdocs")
MODULE_FORMAT = """
{heading} {name}

{doc}

{settings}

{endstring}\n"""

class Module:
    name = ""
    doc = ""
    endstring = ""

    def __init__(self, cls, neighbours, module_name, module, heading):
        self.settings = []
        self.cls = cls
        self.heading = heading

        if neighbours == 1:
            self.name = module_name
        else:
            self.name = "{module}.{cls}".format(module=module_name, cls=self.cls.__name__)

        if self.cls.__doc__ is not None:
            self.doc = self.cls.__doc__
        elif module.__doc__ is not None:
            self.doc = module.__doc__
        else:
            self.doc = ""

        if hasattr(self.cls, "_endstring"):
            self.endstring = self.cls._endstring

        self.get_settings()

    def get_settings(self):
        for setting in self.cls.settings:
            self.settings.append(Setting(self, setting))

    def format_settings(self):
        return "\n".join(map(str, self.settings))

    def __str__(self):
        return MODULE_FORMAT.format(
            name=self.name,
            doc=textwrap.dedent(self.doc),
            settings=self.format_settings(),
            heading=self.heading,
            endstring=self.endstring
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

    def __str__(self):
        attrs = []
        if self.required:
            attrs.append("required")
        if self.default:
            attrs.append("default: `{default}`".format(default=self.default))

        formatted = "* `{name}` ".format(name=self.name)
        if self.doc or attrs:
            formatted += "— "
            if self.doc:
                formatted += self.doc
            if attrs:
                formatted += " ({attrs})".format(attrs=", ".join(attrs))

        return formatted

def get_modules(path=None):
    if path is None:
        path = i3pystatus.get_path()

    modules = []
    for finder, modname, ispkg in pkgutil.iter_modules(path):
        if modname not in IGNORE:
            modules.append(get_module(finder, modname))

    return modules

def get_module(finder, modname):
    fullname = "i3pystatus.{modname}".format(modname=modname)
    return (modname, finder.find_loader(fullname)[0].load_module(fullname))

def get_all(module_path, heading, finder=None):
    mods = []
    if finder is None:
        finder = i3pystatus.ClassFinder(i3pystatus.Module)

    for name, module in get_modules(module_path):
        classes = finder.search_module(module)

        for cls in classes:
            mods.append(Module(cls, neighbours=len(classes), module_name=name, module=module, heading=heading))

    return sorted(mods, key=lambda module: module.name)

def generate_doc_for_module(module_path, heading="###", finder=None):
    return "".join(map(str, get_all(module_path, heading, finder)))

with open("README.tpl.md", "r") as template:

    tpl = template.read()
    tpl = tpl.replace("!!module_doc!!", generate_doc_for_module(i3pystatus.__path__))
    finder = i3pystatus.ClassFinder(baseclass=i3pystatus.mail.Backend)
    tpl = tpl.replace("!!i3pystatus.mail!!", generate_doc_for_module(i3pystatus.mail.__path__, "###", finder).replace("\n", "\n> "))

    print(tpl)

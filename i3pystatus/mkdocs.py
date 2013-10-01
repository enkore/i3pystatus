#!/usr/bin/env python

import sys
import io
import pkgutil
from collections import namedtuple
import textwrap

import i3pystatus
import i3pystatus.mail

from .core.imputil import ClassFinder

IGNORE = ("__main__", "mkdocs", "core")
MODULE_FORMAT = """
{heading} {name}

{doc}

__Settings:__

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
            self.name = "{module}.{cls}".format(
                module=module_name, cls=self.cls.__name__)

        self.doc = self.cls.__doc__ or module.__doc__ or ""

        if hasattr(self.cls, "_endstring"):
            self.endstring = self.cls._endstring

        self.read_settings()

    def read_settings(self):
        for setting in self.cls.settings:
            self.settings.append(Setting(self.cls, setting))

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
    doc = ""
    required = False
    default = sentinel = object()

    def __init__(self, cls, setting):
        if isinstance(setting, tuple):
            self.name = setting[0]
            self.doc = setting[1]
        else:
            self.name = setting

        if setting in cls.required:
            self.required = True
        elif hasattr(cls, self.name):
            self.default = getattr(cls, self.name)

    def __str__(self):
        attrs = []
        if self.required:
            attrs.append("required")
        if self.default is not self.sentinel:
            attrs.append("default: `{default}`".format(default=self.default))

        formatted = "* `{name}` ".format(name=self.name)
        if self.doc or attrs:
            formatted += "— "
            if self.doc:
                formatted += self.doc
            if attrs:
                formatted += " ({attrs})".format(attrs=", ".join(attrs))

        return formatted


def get_modules(path):
    modules = []
    for finder, modname, ispkg in pkgutil.iter_modules(path):
        if modname not in IGNORE:
            modules.append(get_module(finder, modname))
    return modules


def get_module(finder, modname):
    fullname = "i3pystatus.{modname}".format(modname=modname)
    return (modname, finder.find_loader(fullname)[0].load_module(fullname))


def get_all(module_path, heading, finder=None, ignore=None):
    mods = []
    if not finder:
        finder = ClassFinder(i3pystatus.Module)

    for name, module in get_modules(module_path):
        classes = finder.search_module(module)
        found = []
        for cls in classes:
            if cls.__name__ not in found:
                found.append(cls.__name__)
                mods.append(
                    Module(cls, neighbours=len(classes), module_name=name, module=module, heading=heading))

    return sorted(mods, key=lambda module: module.name)


def generate_doc_for_module(module_path, heading="###", finder=None, ignore=None):
    return "".join(map(str, get_all(module_path, heading, finder, ignore or [])))

with open("README.tpl.md", "r") as template:
    tpl = template.read()
    tpl = tpl.replace(
        "!!module_doc!!", generate_doc_for_module(i3pystatus.__path__))
    finder = ClassFinder(baseclass=i3pystatus.mail.Backend)
    tpl = tpl.replace("!!i3pystatus.mail!!", generate_doc_for_module(
        i3pystatus.mail.__path__, "###", finder, ["Backend"]).replace("\n", "\n> "))
    with open("README.md", "w") as output:
        output.write(tpl + "\n")

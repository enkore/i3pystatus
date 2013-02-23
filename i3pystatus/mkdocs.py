#!/usr/bin/env python

import sys
import io
import pkgutil
from collections import namedtuple

import i3pystatus

IGNORE = ("__main__", "mkdocs")

class Module:
    name = ""
    doc = ""
    settings = []

class Setting:
    name = ""
    doc = ""
    required = False
    default = None

#finder = ClassFinder(baseclass=Module, exclude=[Module, IntervalModule, AsyncModule])
finder = i3pystatus.ModuleFinder()

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

def get_modules():
    modules = []
    for finder, modname, ispkg in pkgutil.iter_modules(i3pystatus.get_path()):
        if modname not in IGNORE:
            modules.append(get_module(finder, modname))

    return modules

def get_module(finder, modname):
    fullname = "i3pystatus.{modname}".format(modname=modname)
    return (modname, finder.find_loader(fullname)[0].load_module(fullname))

def get_settings(cls):
    settings = []

    for setting in cls.settings:
        s = Setting()
        if isinstance(setting, tuple):
            s.name = setting[0]
            s.doc = setting[1]
        else:
            s.name = setting

        if setting in cls.required:
            s.required = True
        elif hasattr(cls, s.name):
            s.default = getattr(cls, s.name)

        settings.append(s)

    return settings

def get_all():
    mods = []

    for name, module in get_modules():
        classes = finder.search_module(module)

        for cls in classes:
            m = Module()

            if len(classes) == 1:
                m.name = name
            else:
                m.name = "{module}.{cls}".format(module=name, cls=cls.__name__)

            if hasattr(cls, "__doc__"):
                m.doc = cls.__doc__
            elif hasattr(module, "__doc__"):
                m.doc = module.__doc__

            m.settings = get_settings(cls)

            mods.append(m)

    return mods

def format_settings(settings):
    return "\n".join((format_setting(setting) for setting in settings))

def format_setting(setting):
    attrs = []
    if setting.required:
        attrs.append("required")
    if setting.default:
        attrs.append("default: {default}".format(default=setting.default))

    formatted = "* {name} ".format(name=setting.name)
    if setting.doc or attrs:
        formatted += "— "
        if setting.doc:
            formatted += setting.doc
        if attrs:
            formatted += " ({attrs})".format(attrs=", ".join(attrs))

    return formatted

def write_mods(f, mods):
    for mod in mods:
        f.write("""
### {name}

{doc}

{settings}\n""".format(
            name=mod.name,
            doc=trim(mod.doc),
            settings=format_settings(mod.settings)
        ))

with open("template.md", "r") as template:
    tpl = template.read()

    f = io.StringIO()
    write_mods(f, get_all())

    print(tpl.replace("!!module_doc!!", f.getvalue()))


#    return [finder.search_module]
#    mods = []
#
 #   for modname, module in modules:
  #      classes = finder.search_module(module)
#
#
#
 #       mods.append(get_mod(modname))
  #      mods.append(mod(
   #         name=modname,
    #        docstring=module.__doc__ if hasattr(module, "__doc__") else "",
     #       settings=get_settings(module)
      #  ))
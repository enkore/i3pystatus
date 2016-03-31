
import pkgutil
import importlib

import sphinx.application
from docutils.parsers.rst import Directive
from docutils.nodes import paragraph
from docutils.statemachine import StringList

import i3pystatus.core.settings
import i3pystatus.core.modules
from i3pystatus.core.imputil import ClassFinder
from i3pystatus.core.color import ColorRangeModule

IGNORE_MODULES = ("__main__", "core", "tools")


def is_module(obj):
    return (isinstance(obj, type)
            and issubclass(obj, i3pystatus.core.settings.SettingsBase)
            and not obj.__module__.startswith("i3pystatus.core."))


def fail_on_missing_dependency_hints(obj, lines):
    # We can automatically check in some cases if we forgot something
    if issubclass(obj, ColorRangeModule):
        if all("colour" not in line for line in lines):
            raise ValueError(">>> Module <{}> uses ColorRangeModule and should document it <<<\n"
                             "> Requires the PyPI package ``colour``".format(obj.__name__))


def check_settings_consistency(obj, settings):
    errs = []
    for setting in settings:
        if not setting.required and setting.default is setting.sentinel:
            errs.append("<" + setting.name + ">")
    if errs:
        raise ValueError(">>> Module <{}> has non-required setting(s) {} with no default! <<<\n"
                         .format(obj.__name__, ", ".join(errs)))


def process_docstring(app, what, name, obj, options, lines):
    class Setting:
        doc = ""
        required = False
        default = sentinel = object()
        empty = object()

        def __init__(self, cls, setting):
            if isinstance(setting, tuple):
                self.name = setting[0]
                self.doc = setting[1]
            else:
                self.name = setting
            if self.name in cls.required:
                self.required = True
            elif hasattr(cls, self.name):
                default = getattr(cls, self.name)
                if isinstance(default, str) and not len(default)\
                        or default is None:
                    default = self.empty
                self.default = default

        def __str__(self):
            attrs = []
            if self.required:
                attrs.append("required")
            if self.default not in [self.sentinel, self.empty]:
                attrs.append("default: ``{default}``".format(default=self.default))
            if self.default is self.empty:
                attrs.append("default: *empty*")

            formatted = "* **{name}** {attrsf} {doc}".format(
                name=self.name,
                doc="– " + self.doc if self.doc else "",
                attrsf=" ({attrs})".format(attrs=", ".join(attrs)) if attrs else "")

            return formatted

    if is_module(obj) and obj.settings:
        fail_on_missing_dependency_hints(obj, lines)

        lines.append(".. rubric:: Settings")
        lines.append("")

        settings = [Setting(obj, setting) for setting in obj.settings]

        lines += map(str, settings)

        check_settings_consistency(obj, settings)

        lines.append("")


def process_signature(app, what, name, obj, options, signature, return_annotation):
    if is_module(obj):
        return ("", return_annotation)


def get_modules(path, package):
    modules = []
    for finder, modname, is_package in pkgutil.iter_modules(path):
        if modname not in IGNORE_MODULES:
            modules.append(get_module(finder, modname, package))
    return modules


def get_module(finder, modname, package):
    fullname = "{package}.{modname}".format(package=package, modname=modname)
    return (modname, finder.find_loader(fullname)[0].load_module(fullname))


def get_all(module_path, modname, basecls):
    mods = []

    finder = ClassFinder(basecls)

    for name, module in get_modules(module_path, modname):
        classes = finder.get_matching_classes(module)
        found = []
        for cls in classes:
            if cls.__name__ not in found:
                found.append(cls.__name__)
                mods.append((module.__name__, cls.__name__))

    return sorted(mods, key=lambda module: module[0])


def generate_automodules(path, name, basecls):
    modules = get_all(path, name, basecls)

    contents = []

    for mod in modules:
        contents.append("*  :py:mod:`~{}`".format(mod[0]))
    contents.append("")

    for mod in modules:
        contents.append(".. _{}:\n".format(mod[0].split(".")[-1]))
        contents.append(".. automodule:: {}".format(mod[0]))
        contents.append("    :members: {}\n".format(mod[1]))

    return contents


class AutogenDirective(Directive):
    required_arguments = 2
    has_content = True

    def run(self):
        # Raise an error if the directive does not have contents.
        self.assert_has_content()

        modname = self.arguments[0]
        modpath = importlib.import_module(modname).__path__
        basecls = getattr(i3pystatus.core.modules, self.arguments[1])

        contents = []
        for e in self.content:
            contents.append(e)
        contents.append("")
        contents.extend(generate_automodules(modpath, modname, basecls))

        node = paragraph()
        self.state.nested_parse(StringList(contents), 0, node)
        return [node]


def setup(app: sphinx.application.Sphinx):

    app.add_directive("autogen", AutogenDirective)
    app.connect("autodoc-process-docstring", process_docstring)
    app.connect("autodoc-process-signature", process_signature)

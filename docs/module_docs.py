
import pkgutil

import sphinx.application

import i3pystatus.core.settings


def is_module(obj):
    return isinstance(obj, type) \
            and issubclass(obj, i3pystatus.core.settings.SettingsBase) \
            and not obj.__module__.startswith("i3pystatus.core.")



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

            if setting in cls.required:
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

            formatted = "* **{name}** – {doc}".format(name=self.name, doc=self.doc)
            if attrs:
                formatted += " ({attrs})".format(attrs=", ".join(attrs))

            return formatted


    if is_module(obj):
        lines.append(".. rubric:: Settings")
        lines.append("")

        for setting in obj.settings:
            lines.append(str(Setting(obj, setting)))


def process_signature(app, what, name, obj, options, signature, return_annotation):
    if is_module(obj):
        return ("", return_annotation)


def source_read(app, docname, source):
    ignore_modules = ("__main__", "mkdocs", "core")

    def get_modules(path):
        modules = []
        for finder, modname, is_pkg in pkgutil.iter_modules(path):
            if modname not in ignore_modules:
                modules.append("i3pystatus." + modname)
        return modules

    if docname == "i3pystatus":
        modules = sorted(get_modules(i3pystatus.__path__))

        for mod in modules:
            # sphinx seems to discard .append()ed items
            source[0] += "    *  :py:class:`~{}`\n".format(mod)

        for mod in modules:
            source[0] += (".. automodule:: " + mod + "\n" +
                          "    :members:\n\n")


def setup(app: sphinx.application.Sphinx):
    app.connect("source-read", source_read)
    app.connect("autodoc-process-docstring", process_docstring)
    app.connect("autodoc-process-signature", process_signature)

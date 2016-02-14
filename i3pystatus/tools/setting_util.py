#!/usr/bin/env python
import glob
import inspect
import os
import getpass
import sys
import signal
import pkgutil
from collections import defaultdict, OrderedDict

import keyring

import i3pystatus
from i3pystatus import Module, SettingsBase
from i3pystatus.core import ClassFinder
from i3pystatus.core.exceptions import ConfigInvalidModuleError


def signal_handler(signal, frame):
    sys.exit(0)


def get_int_in_range(prompt, _range):
    while True:
        try:
            answer = input(prompt)
        except EOFError:
            print()
            sys.exit(0)
        try:
            n = int(answer.strip())
            if n in _range:
                return n
            else:
                print("Value out of range!")
        except ValueError:
            print("Invalid input!")


def enumerate_choices(choices):
    lines = []
    for index, choice in enumerate(choices, start=1):
        lines.append(" %d - %s\n" % (index, choice))
    return "".join(lines)


def get_modules():
    for importer, modname, ispkg in pkgutil.iter_modules(i3pystatus.__path__):
        if modname not in ["core", "tools"]:
            yield modname


def get_credential_modules():
    verbose = "-v" in sys.argv

    protected_settings = SettingsBase._SettingsBase__PROTECTED_SETTINGS
    class_finder = ClassFinder(Module)
    credential_modules = defaultdict(dict)
    for module_name in get_modules():
        try:
            module = class_finder.get_module(module_name)
            clazz = class_finder.get_class(module)
        except (ImportError, ConfigInvalidModuleError):
            if verbose:
                print("ImportError while importing", module_name)
            continue

        members = [m[0] for m in inspect.getmembers(clazz) if not m[0].startswith('_')]
        if any([hasattr(clazz, setting) for setting in protected_settings]):
            credential_modules[clazz.__name__]['credentials'] = list(set(protected_settings) & set(members))
            credential_modules[clazz.__name__]['key'] = "%s.%s" % (clazz.__module__, clazz.__name__)
        elif hasattr(clazz, 'required'):
            protected = []
            required = getattr(clazz, 'required')
            for setting in protected_settings:
                if setting in required:
                    protected.append(setting)
            if protected:
                credential_modules[clazz.__name__]['credentials'] = protected
                credential_modules[clazz.__name__]['key'] = "%s.%s" % (clazz.__module__, clazz.__name__)
    return credential_modules


def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("""%s - part of i3pystatus
This allows you to edit keyring-protected settings of
i3pystatus modules, which are stored globally (independent
of your i3pystatus configuration) in your keyring.

Options:
    -l: list all stored settings (no values are printed)
    -v: print informational messages
""" % os.path.basename(sys.argv[0]))

    credential_modules = get_credential_modules()

    if "-l" in sys.argv:
        for name, module in credential_modules.items():
            print(name)
            for credential in module['credentials']:
                if keyring.get_password("%s.%s" % (module['key'], credential), getpass.getuser()):
                    print(" - %s: set" % credential)
                else:
                    print(" - %s: unset" % credential)
        return

    choices = list(credential_modules.keys())
    prompt = "Choose a module to edit:\n"
    prompt += enumerate_choices(choices)
    prompt += "> "

    index = get_int_in_range(prompt, range(1, len(choices) + 1))
    module_name = choices[index - 1]
    module = credential_modules[module_name]

    prompt = "Choose setting of %s to edit:\n" % module_name
    prompt += enumerate_choices(module["credentials"])
    prompt += "> "

    choices = module['credentials']
    index = get_int_in_range(prompt, range(1, len(choices) + 1))
    setting = choices[index - 1]

    answer = getpass.getpass("Enter value for %s:\n> " % setting)
    answer2 = getpass.getpass("Re-enter value\n> ")
    if answer == answer2:
        key = "%s.%s" % (module['key'], setting)
        keyring.set_password(key, getpass.getuser(), answer)
        print("%s set!" % setting)
    else:
        print("Values don't match - nothing set.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import glob
import inspect
import os
import keyring
import getpass
import sys
import signal
from i3pystatus import Module, SettingsBase
from i3pystatus.core import ClassFinder
from collections import defaultdict, OrderedDict

def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def get_int_in_range(prompt, _range):
    while True:
        answer = input(prompt)
        try:
            n = int(answer.strip())
            if n in _range:
                return n
            else:
                print("Value out of range!")
        except ValueError:
            print("Invalid input!")

modules = [os.path.basename(m.replace('.py', ''))
           for m in glob.glob(os.path.join(os.path.dirname(__file__), "i3pystatus", "*.py"))
           if not os.path.basename(m).startswith('_')]

protected_settings = SettingsBase._SettingsBase__PROTECTED_SETTINGS
class_finder = ClassFinder(Module)
credential_modules = defaultdict(dict)
for module_name in modules:
    try:
        module = class_finder.get_module(module_name)
        clazz = class_finder.get_class(module)
        members = [m[0] for m in inspect.getmembers(clazz) if not m[0].startswith('_')]
        if any([hasattr(clazz, setting) for setting in protected_settings]):
            credential_modules[clazz.__name__]['credentials'] = list(set(protected_settings) & set(members))
            credential_modules[clazz.__name__]['key'] = "%s.%s" % (clazz.__module__, clazz.__name__)
    except ImportError:
        continue

choices = [k for k in credential_modules.keys()]
for idx, module in enumerate(choices, start=1):
    print("%s - %s" % (idx, module))

index = get_int_in_range("Choose module:\n> ", range(1, len(choices) + 1))
module_name = choices[index - 1]
module = credential_modules[module_name]

for idx, setting in enumerate(module['credentials'], start=1):
    print("%s - %s" % (idx, setting))

choices = module['credentials']
index = get_int_in_range("Choose setting for %s:\n> " % module_name, range(1, len(choices) + 1))
setting = choices[index - 1]

answer = getpass.getpass("Enter value for %s:\n> " % setting)
answer2 = getpass.getpass("Re-enter value\n> ")
if answer == answer2:
    key = "%s.%s" % (module['key'], setting)
    keyring.set_password(key, getpass.getuser(), answer)
    print("%s set!" % setting)
else:
    print("Values don't match - nothing set.")

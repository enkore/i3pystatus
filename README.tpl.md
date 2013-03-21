<!--
    Always edit README.tpl.md and create README.md by running
    python -m i3pystatus.mkdocs
    You can also let the maintainer do the latter :)
-->

# i3pystatus

i3pystatus is a (hopefully growing) collection of python scripts for 
status output compatible to i3status / i3bar of the i3 window manager.

## Installation

### From PyPI package [i3pystatus](https://pypi.python.org/pypi/i3pystatus)

    pip install i3pystatus

### Packages for your OS

    * [Arch Linux](https://aur.archlinux.org/packages/i3pystatus-git/)

## Configuration

You can keep your config file at various places, i3pystatus will look
for it in these places:

    ~/.i3pystatus.py
    ~/.i3/i3pystatus.py
    ~/.config/i3pystatus.py
    $XDG_CONFIG_HOME/i3pystatus.py
    /etc/i3pystatus.py
    /etc/xdg/i3pystatus.py
    $XDG_CONFIG_DIRS/i3pystatus.py

A sample configuration file is `i3pystatus/__main__.py.dist`

Also change your i3wm config to the following:

    # i3bar
    bar {
        status_command    i3pystatus
        position          top
        workspace_buttons yes
    }

## Modules

Many modules let you modify the output via a
[format string](http://docs.python.org/3/library/string.html#formatstrings).

!!module_doc!!

## Contribute

To contribute a module, make sure it uses one of the Module classes. Most modules
use IntervalModule, which just calls a function repeatedly in a specified interval.

The output attribute should be set to a dictionary which represents your modules output,
the protocol is documented [here](http://i3wm.org/docs/i3bar-protocol.html).

Please add an example for how to configure it to `__main__.py.dist`. It should be
a python class that can be registered with the `I3statusHandler` class. Also don't
forget to add yourself to the LICENSE file.

**Patches and pull requests are very welcome :-)**

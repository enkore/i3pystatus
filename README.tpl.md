# i3pystatus

i3pystatus is a (hopefully growing) collection of python scripts for 
status output compatible to i3status / i3bar of the i3 window manager.

## Version 3

Version 3 has been merged into master recently, please check out if your config still works,
as many modules have been reworked (mostly added options) and the new settings system is in-place.
For examples how it works, take a look at the __main__.py.dist file with some examples.

## Installation

To install it, follow these steps:

    cd ~/.config/i3status/
    git clone git@github.com:janoliver/i3pystatus contrib
    cd contrib/i3pystatus
    cp __main__.py.dist __main__.py

Add the following to `~/.config/i3status/config`:

    general {
        output_format = "i3bar"
        colors = true
        interval = 5
    }

Change your i3wm config to the following:

    # i3bar
    bar {
        status_command    cd ~/.config/i3status/contrib ; i3status | python -m i3pystatus
        position          top
        workspace_buttons yes
    }

And finally adjust the settings in `~/.config/i3status/contrib/i3pystatus/__main__.py`
as you like. 

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

# i3pystatus

i3pystatus is a (hopefully growing) collection of python scripts for 
status output compatible to i3status / i3bar of the i3 window manager.

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


### batterychecker

This class uses the /proc/acpi/battery interface to check for the
battery status

* battery_ident —  (default: BAT0)

### clock

This class shows a clock

* format — stftime format string

### mail



* backends —  (required)
* color 

### modsde

This class returns i3status parsable output of the number of
unread posts in any bookmark in the mods.de forums.

* format — Use {unread} as the formatter for number of unread posts (default: {unread} new posts in bookmarks)
* offset — subtract number of posts before output
* color —  (default: #7181fe)
* username —  (required)
* password —  (required)

### regex

Simple regex file watcher

* format — format string used for output (default: {0})
* regex —  (required)
* file — file to search for regex matches
* flags — Python.re flags


## Contribute

To contribute a module, make sure it uses one of the Module classes. Most modules
use IntervalModule, which just calls a function repeatedly in a specified interval.

The output attribute should be set to a dictionary which represents your modules output,
the protocol is documented [here](http://i3wm.org/docs/i3bar-protocol.html).

Please add an example for how to configure it to `__main__.py.dist`. It should be
a python class that can be registered with the `I3statusHandler` class. Also don't
forget to add yourself to the LICENSE file.

**Patches and pull requests are very welcome :-)**


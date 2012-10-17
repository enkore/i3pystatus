# i3pystatus

i3pystatus is a (hopefully growing) collection of python scripts for 
status output compatible to i3status / i3bar of the i3 window manager.

## Installation

To install it, follow these steps:

    cd ~/.config/i3status/
    git clone git@github.com:janoliver/i3pystatus contrib
    cd contrib
    cp wrapper.py.dist wrapper.py

Add the following to `~/.config/i3status/config`:

    general {
        output_format = "i3bar"
        colors = true
        interval = 5
    }

Change your i3wm config to the following:

    # i3bar
    bar {
        status_command    i3status | python2 ~/.config/i3status/contrib/wrapper.py
        position          top
        workspace_buttons yes
    }

And finally adjust the settings in `~/.config/i3status/contrib/wrapper.py`
as you like. 

## Contribute

To contribute a script, make sure it has a function `output()` that outputs
valid json code that can be interpreted by i3status. The protocol is documented
here: [i3status Protocol](http://i3wm.org/docs/i3bar-protocol.html).

Please add an example for how to configure it to `wrapper.py.dist`. It should be
a python class that can be registered with the `I3StatusHandler` class.
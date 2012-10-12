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

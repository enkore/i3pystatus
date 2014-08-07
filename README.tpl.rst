..  Always edit README.tpl.rst. Do not change the module reference manually.

i3pystatus
==========

.. image:: https://travis-ci.org/enkore/i3pystatus.svg?branch=master
    :target: https://travis-ci.org/enkore/i3pystatus

i3pystatus is a (hopefully growing) collection of python scripts for 
status output compatible to i3status / i3bar of the i3 window manager.

Installation
------------

.. admonition:: Note

    i3pystatus requires Python 3.2 or newer and is not compatible with
    Python 2.x. Some modules require additional dependencies
    documented below (see `Modules`_).

From PyPI package `i3pystatus <https://pypi.python.org/pypi/i3pystatus>`_
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

::

    pip install i3pystatus

Packages for your OS
++++++++++++++++++++

* `Arch Linux <https://aur.archlinux.org/packages/i3pystatus-git/>`_

Release Notes
-------------

Contributors
++++++++++++

* aaron-lebo
* afics
* al45tair
* Argish42
* Arvedui
* atalax
* cganas
* crwood
* dubwoc
* enkore (current maintainer)
* gwarf
* janoliver (former maintainer)
* jasonmhite
* jedrz
* jorio
* mekanix
* Mic92
* micha-a-schmidt
* naglis
* philipdexter
* sbrunner
* siikamiika
* talwrii
* tomkenmag
* tomxtobin
* tony
* yemu
* zzatkin

next
++++

* Added `uptime`_ module

3.30
++++

* Added `bitcoin`_ module
* Added `now\_playing`_ module
* Added `reddit`_ module
* Added `shell`_ module
* Core: fixed custom statusline colors not working properly (see issue #74)
* `alsa`_ and `pulseaudio`_: added optional "formated_muted"
  audio is muted.
* `battery`_: add bar formatter, add not_present_text, full_color,
  charging_color, not_present_color settings
* `disk`_: add color and round_size options
* maildir: use os.listdir instead of ls
* `mem`_: add round_size option
* `mpd`_: add color setting
* `mpd`_: add filename formatter
* `mpd`_: next song on right click
* `network`_ and `wireless`_: support interfaces enslaved to a bonding master
* `network`_: detached_down is now True by default
* `network`_: fixed some issues with interface up/down detection
* `parcel`_: added support for Itella (Finnish national postal service)
  setting. If provided, it will be used instead of "format" when the
* `temp`_: add file setting
* `temp`_: fixed issue with Linux kernels 3.15 and newer
* `temp`_: removed color_critical and high_factor options
* `text`_: add cmd_leftclick and cmd_rightclick options
* `weather`_: add colorize option
* `wireless`_: Add quality_bar formatter

3.29
++++

* `network`_: prefer non link-local v6 addresses
* `mail`_: Open email client and refresh email with mouse click
* `disk`_: Add display and critical limit
* `battery`_: fix errors if CURRENT_NOW is not present
* `battery`_: add configurable colors
* `load`_: add configurable colors and limit
* `parcel`_: rewrote DHL tracker
* Add `spotify`_ module

3.28
++++

* **If you're currently using the i3pystatus command to run your i3bar**:
    Replace ``i3pystatus`` command in your i3 configuration with ``python ~/path/to/your/config.py``
* Do not name your script i3pystatus.py or it will break imports.
* New options for `mem`_
* Added `cpu\_usage`_
* Improved error handling
* Removed ``i3pystatus`` binary
* pulseaudio: changed context name to "i3pystatus_pulseaudio"
* Add maildir backend for mails
* Code changes
* Removed DHL tracker of parcel module, because it doesn't work anymore.

3.27
++++

* Add weather module
* Add text module
* PulseAudio module: Add muted/unmuted options

3.26
++++

* Add mem module

3.24
++++

**This release introduced changes that may require manual changes to your
configuration file**

* Introduced TimeWrapper
* battery module: removed remaining\_* formatters in favor of
  TimeWrapper, as it can not only reproduce all the variants removed,
  but can do much more.
* mpd: Uses TimeWrapper for song_length, song_elapsed

Configuration
-------------

The config file is just a normal Python script.

A simple configuration file could look like this (note the additional
dependencies from `network`_, `wireless`_ and `pulseaudio`_ in this
example):

::

    # -*- coding: utf-8 -*-

    import subprocess

    from i3pystatus import Status

    status = Status(standalone=True)

    # Displays clock like this:
    # Tue 30 Jul 11:59:46 PM KW31
    #                          ^-- calendar week
    status.register("clock",
        format="%a %-d %b %X KW%V",)

    # Shows the average load of the last minute and the last 5 minutes
    # (the default value for format is used)
    status.register("load")

    # Shows your CPU temperature, if you have a Intel CPU
    status.register("temp",
        format="{temp:.0f}°C",)

    # The battery monitor has many formatting options, see README for details

    # This would look like this, when discharging (or charging)
    # ↓14.22W 56.15% [77.81%] 2h:41m
    # And like this if full:
    # =14.22W 100.0% [91.21%]
    #
    # This would also display a desktop notification (via dbus) if the percentage
    # goes below 5 percent while discharging. The block will also color RED.
    status.register("battery",
        format="{status}/{consumption:.2f}W {percentage:.2f}% [{percentage_design:.2f}%] {remaining:%E%hh:%Mm}",
        alert=True,
        alert_percentage=5,
        status={
            "DIS": "↓",
            "CHR": "↑",
            "FULL": "=",
        },)

    # This would look like this:
    # Discharging 6h:51m
    status.register("battery",
        format="{status} {remaining:%E%hh:%Mm}",
        alert=True,
        alert_percentage=5,
        status={
            "DIS":  "Discharging",
            "CHR":  "Charging",
            "FULL": "Bat full",
        },)

    # Displays whether a DHCP client is running
    status.register("runwatch",
        name="DHCP",
        path="/var/run/dhclient*.pid",)

    # Shows the address and up/down state of eth0. If it is up the address is shown in
    # green (the default value of color_up) and the CIDR-address is shown
    # (i.e. 10.10.10.42/24).
    # If it's down just the interface name (eth0) will be displayed in red
    # (defaults of format_down and color_down)
    #
    # Note: the network module requires PyPI package netifaces
    status.register("network",
        interface="eth0",
        format_up="{v4cidr}",)

    # Has all the options of the normal network and adds some wireless specific things
    # like quality and network names.
    #
    # Note: requires both netifaces and basiciw
    status.register("wireless",
        interface="wlan0",
        format_up="{essid} {quality:03.0f}%",)

    # Shows disk usage of /
    # Format:
    # 42/128G [86G]
    status.register("disk",
        path="/",
        format="{used}/{total}G [{avail}G]",)

    # Shows pulseaudio default sink volume
    #
    # Note: requires libpulseaudio from PyPI
    status.register("pulseaudio",
        format="♪{volume}",)

    # Shows mpd status
    # Format:
    # Cloud connected▶Reroute to Remain
    status.register("mpd",
        format="{title}{status}{album}",
        status={
            "pause": "▷",
            "play": "▶",
            "stop": "◾",
        },)

    status.run()

Also change your i3wm config to the following:

::

    # i3bar
    bar {
        status_command    python ~/.path/to/your/config/file.py
        position          top
        workspace_buttons yes
    }

Formatting
++++++++++

All modules let you specifiy the exact output formatting using a
`format string <http://docs.python.org/3/library/string.html#formatstrings>`_, which
gives you a great deal of flexibility.

If a module gives you a float, it probably has a ton of
uninteresting decimal places. Use ``{somefloat:.0f}`` to get the integer
value, ``{somefloat:0.2f}`` gives you two decimal places after the
decimal dot

formatp
~~~~~~~

Some modules use an extended format string syntax (the mpd module, for example).
Given the format string below the output adapts itself to the available data.

::

    [{artist}/{album}/]{title}{status}

Only if both the artist and album is known they're displayed. If only one or none
of them is known the entire group between the brackets is excluded.

"is known" is here defined as "value evaluating to True in Python", i.e. an empty
string or 0 (or 0.0) counts as "not known".

Inside a group always all format specifiers must evaluate to true (logical and).

You can nest groups. The inner group will only become part of the output if both
the outer group and the inner group are eligible for output.

TimeWrapper
~~~~~~~~~~~

Some modules that output times use TimeWrapper to format these. TimeWrapper is
a mere extension of the standard formatting method.

The time format that should be used is specified using the format specifier, i.e.
with some_time being 3951 seconds a format string like ``{some_time:%h:%m:%s}``
would produce ``1:5:51``.

* ``%h``, ``%m`` and ``%s`` are the hours, minutes and seconds without
  leading zeros (i.e. 0 to 59 for minutes and seconds)
* ``%H``, ``%M`` and ``%S`` are padded with a leading zero to two digits,
  i.e. 00 to 59
* ``%l`` and ``%L`` produce hours non-padded and padded but only if hours
  is not zero.  If the hours are zero it produces an empty string.
* ``%%`` produces a literal %
* ``%E`` (only valid on beginning of the string) if the time is null,
  don't format anything but rather produce an empty string. If the
  time is non-null it is removed from the string.
* When the module in question also uses formatp, 0 seconds counts as
  "not known".
* The formatted time is stripped, i.e. spaces on both ends of the
  result are removed.

Modules
-------

:System: `clock`_ - `disk`_ - `load`_ - `mem`_  - `cpu\_usage`_
:Audio: `alsa`_ - `pulseaudio`_
:Hardware: `battery`_ - `backlight`_ - `temp`_
:Network: `network`_ - `wireless`_
:Music: `now\_playing`_ - `mpd`_
:Websites & stuff: `weather`_ - `bitcoin`_ - `reddit`_ - `parcel`_
:Other: `mail`_ - `pyload`_ -  `text`_ 
:Advanced: `file`_ - `regex`_ - `runwatch`_ - `shell`_

!!module_doc!!

Contribute
----------

To contribute a module, make sure it uses one of the Module classes. Most modules
use IntervalModule, which just calls a function repeatedly in a specified interval.

The output attribute should be set to a dictionary which represents your modules output,
the protocol is documented `here <http://i3wm.org/docs/i3bar-protocol.html>`_.

To update this readme run ``python -m i3pystatus.mkdocs`` in the
repository root and you're done :)

Developer documentation is available in the source code and `here
<http://i3pystatus.readthedocs.org/en/latest/>`_.

**Patches and pull requests are very welcome :-)**

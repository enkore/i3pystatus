..  Always edit README.tpl.rst. Do not change the module reference manually.

i3pystatus
==========

.. image:: https://travis-ci.org/enkore/i3pystatus.svg?branch=master
    :target: https://travis-ci.org/enkore/i3pystatus

i3pystatus is a (hopefully growing) collection of python scripts for 
status output compatible to i3status / i3bar of the i3 window manager.

Installation
------------

.. note:: Supported Python versions

    i3pystatus requires Python 3.2 or newer and is not compatible with
    Python 2.x. Some modules require additional dependencies
    documented in the docs.

From PyPI package `i3pystatus <https://pypi.python.org/pypi/i3pystatus>`_
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

::

    pip install i3pystatus

Packages for your OS
++++++++++++++++++++

* `Arch Linux <https://aur.archlinux.org/packages/i3pystatus/>`_ (stable
  release)
* `Arch Linux <https://aur.archlinux.org/packages/i3pystatus-git/>`_ (latest
  version)

Documentation
-------------

`All further user documentation has been moved here. <http://i3pystatus.readthedocs.org/en/latest/index.html>`_


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
* bparmentier
* cganas
* crwood
* dubwoc
* enkore (current maintainer)
* facetoe
* gwarf
* hobarrera
* janoliver (former maintainer)
* jasonmhite
* jedrz
* jorio
* kageurufu
* mekanix
* Mic92
* micha-a-schmidt
* naglis
* philipdexter
* rampage644 
* sbrunner
* siikamiika
* simon04
* talwrii
* teto
* tomkenmag
* tomxtobin
* tony
* xals
* yemu
* zzatkin

next
++++

* Added uptime module
* cpu\_usage: Add multicore support
* cpu\_usage\_bar: Add multicore support
* network: Add unknown_up setting
* parcel: Document lxml dependency
* Added network\_traffic module
* mpd: Play song on left click even if stopped
* Fixed issues with internet-related modules
* battery: Added no_text_full option
* Unexpected exceptions are now displayed in the status bar
* mail: db_path option made optional
* Core: added mouse wheel handling for upcoming i3 version
* alsa: mouse wheel changes volume
* pulseaudio: Added color_muted and color_unmuted options
* Added network_graph module
* New module mixin: ip3ystatus.core.color.ColorRangeModule
* Added cpu_usage_graph module
* pulseaudio: Added step, bar_type, multi_colors, vertical_bar_width options
* pulseaudio: Scroll to change master volume, right click to (un)mute
* Added pomodoro module
* Added cmus module

3.30
++++

* Added bitcoin module
* Added now\_playing module
* Added reddit module
* Added shell module
* Core: fixed custom statusline colors not working properly (see issue #74)
* alsa and pulseaudio: added optional "formated_muted"
  audio is muted.
* battery: add bar formatter, add not_present_text, full_color,
  charging_color, not_present_color settings
* disk: add color and round_size options
* maildir: use os.listdir instead of ls
* mem: add round_size option
* mpd: add color setting
* mpd: add filename formatter
* mpd: next song on right click
* network and wireless: support interfaces enslaved to a bonding master
* network: detached_down is now True by default
* network: fixed some issues with interface up/down detection
* parcel: added support for Itella (Finnish national postal service)
  setting. If provided, it will be used instead of "format" when the
* temp: add file setting
* temp: fixed issue with Linux kernels 3.15 and newer
* temp: removed color_critical and high_factor options
* text: add cmd_leftclick and cmd_rightclick options
* weather: add colorize option
* wireless: Add quality_bar formatter

3.29
++++

* network: prefer non link-local v6 addresses
* mail: Open email client and refresh email with mouse click
* disk: Add display and critical limit
* battery: fix errors if CURRENT_NOW is not present
* battery: add configurable colors
* load: add configurable colors and limit
* parcel: rewrote DHL tracker
* Add spotify module

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

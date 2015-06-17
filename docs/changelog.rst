
Changelog
=========

master branch
+++++++++++++

* Errors can now be logged to ``~/.i3pystatus-<pid>``
    - See :ref:`logging`
* Added new callback system
    - See :ref:`callbacks`
* Added credentials storage
    - See :ref:`credentials`
* Added deadbeef module
* Added github module
* Added whosonlocation module
* Added openvpn module
* backlight: add xbacklight support for changing brightness with mouse wheel
* battery: added support for depleted batteries
* battery: added support for multiple batteries
* battery: added option to treat all batteries as one large battery (ALL)
* cpu_usage: removed hard coded interval setting
* cpu_usage_bar: fixed wrong default setting
* clock: removed optional pytz dependency
* network: cycle available interfaces on click
* network: centralized network modules
    - Removed ``network_graph``
    - Removed ``network_traffic``
    - Removed ``wireless``
* network: ``basiciw`` is only required if it is used (wireless)
* network: ``psutil`` is only required if it is used (traffic)
* network: scrolling changes displayed interface
* network: fixed bug that prevented color_up being shown if the user is not using network_traffic
* network: various other enhancements
* notmuch: fixed sync issue with database
* now_playing: added custom format and color when no player is running
* now_playing: differentiates between D-Bus errors and no players running
* now_playing: fixed D-Bus compatibility with players
* mail: added capability to display unread messages per account individually
* mpd: various enhancements and fixes
* pulseaudio: detect default sink changes in pulseaudio
* reddit: can open users mailbox now
* shell: fixed module not stripping newlines
* spotify: check for metadata on start
* temp: alert temperatures
* weather: removed pywapi dependency
* weather: add min_temp and max_temp formatters for daily min/max temperature

3.32
++++

* Added keyboard_locks module
* Added pianobar module
* Added uname module
* cmus: enhanced artist/title detection from filenames
* cmus: fixed issue when cmus is not running
* mpd: added text_len and truncate_fields options to truncate long artist, album or song names
* network_traffic: added hide_down and format_down options
* pomodoro: added format option
* pomodoro: reset timer on left click
* pulseaudio: fix rounding error of percentage volume

3.31
++++

* Added cmus module
* Added cpu_usage_graph module
* Added network_graph module
* Added network_traffic module
* Added pomodoro module
* Added uptime module
* alsa: mouse wheel changes volume
* battery: Added no_text_full option
* Core: added mouse wheel handling for upcoming i3 version
* cpu\_usage: Add multicore support
* cpu\_usage\_bar: Add multicore support
* Fixed issues with internet-related modules
* mail: db_path option made optional
* mpd: Play song on left click even if stopped
* network: Add unknown_up setting
* New module mixin: ip3ystatus.core.color.ColorRangeModule
* parcel: Document lxml dependency
* pulseaudio: Added color_muted and color_unmuted options
* pulseaudio: Added step, bar_type, multi_colors, vertical_bar_width options
* pulseaudio: Scroll to change master volume, right click to (un)mute
* Unexpected exceptions are now displayed in the status bar


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
* New options for mem
* Added cpu_usage
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


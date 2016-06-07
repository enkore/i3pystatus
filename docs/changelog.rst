
Changelog
=========

master branch
+++++++++++++

.. _r3.35:

3.34 (2016-02-14)
+++++++++++++++++

* New modules
    - :py:mod:`.moon`: Display moon phase
    - :py:mod:`.online`: Display internet connectivity
    - :py:mod:`.xkblayout`: View and change keyboard layout
    - :py:mod:`.plexstatus`: View status of Plex Media Server
    - :py:mod:`.iinet`: View iiNet internet usage
    - :py:mod:`.gpu_mem`, :py:mod:`.gpu_temp`: View memory and temperature stats of nVidia cards
    - :py:mod:`.solaar`: Show battery status of Solaar / Logitech Unifying devices
    - :py:mod:`.zabbix`: Alerts watcher for the Zabbix enterprise network monitor
    - :py:mod:`.sge`: Sun Grid Engine (SGE) monitor
    - :py:mod:`.timer`: Timer
    - :py:mod:`.syncthing`: Syncthing monitor and control
    - :py:mod:`.vk`: Displays number of messages in VKontakte
* Applications started from click events don't block other click events now
* Fixed crash with desktop notifications when python-gobject is installed, but no notification daemon is running
* Log file name is now an option (``logfile`` of :py:class:`.Status`)
* Server used for checking internet connectivity is now an option (``internet_check`` of :py:class:`.Status`)
* Added double click support for click events
* Formatter data is now available with most modules for program callbacks
* Changed default mode to standalone mode
* ``self`` is not passed anymore by default to external Python callbacks (see :py:func:`.get_module`)
* :py:mod:`.dota2wins`: Now accepts usernames in place of a Steam ID
* dota2wins: Changed win percentage to be a float
* :py:mod:`.uptime`: Added days, hours, minutes, secs formatters
* :py:mod:`.battery`: Added alert command feature (runs a shell
  command when the battery is discharged below a preset threshold)
* :py:mod:`.spotify`: Added status, format\_not\_running and color\_not\_running settings, rewrite
* :py:mod:`.cmus`: Added status, format\_not\_running and color\_not\_running settings
* :py:mod:`.cmus`: Fixed bug that sometimes lead to empty output
* :py:mod:`.shell`: Added formatting capability
* :py:mod:`.cpu_usage`: Added color setting
* :py:mod:`.mpd`: Added hide\_inactive settings
* mpd: Fixed a bug where an active playlist would be assumed, leading to no output
* mpd: Added support for UNIX sockets
* :py:mod:`.updates`: Added yaourt backend
* updates: Can display a working/busy message now
* updates: Additional formatters for every backend (to distinguish pacman vs. AUR updates, for example)
* :py:mod:`.reddit`: Added link\_karma and comment\_karma formatters
* :py:mod:`.openvpn`: Configurable up/down symbols
* openvpn: Rename colour_up/colour_down to color_up/color_down
* openvpn: NetworkManager compatibility
* :py:mod:`.disk`: Improved handling of unmounted drives. Previously
  the free space of the underlying filesystem would be reported if the
  path provided was a directory but not a valid mountpoint. This adds
  a check to first confirm whether a directory is a mountpoint using
  os.path.ismount(), and if not, then runs an os.listdir() to count
  the files; empty directories are considered not mounted. This
  functionality allows for usage on setups with NFS and will not
  report free space of underlying filesystem in cases with local
  mountpoints as path.
* :py:mod:`.battery`: Added ``bar_design`` formatter
* :py:mod:`.alsa`: Implemented optional volume display/setting as in AlsaMixer
* :py:mod:`.pulseaudio`: Fixed bug that created zombies on a click event
* :py:mod:`.backlight`: Fixed bug preventing brightness increase
  
3.33 (2015-06-23)
+++++++++++++++++

* Errors can now be logged to ``~/.i3pystatus-<pid>``
    - See :ref:`logging`
* Added new callback system
    - See :ref:`callbacks`
* Added credentials storage
    - See :ref:`credentials`
* Added :ref:`hints` to support special uses cases
* Added support for Pango markup
* Sending SIGUSR1 to i3pystatus refreshes the bar
    - See :ref:`refresh`
* Modules are refreshed instantly after a callback was handled
* Fixed issue where i3bar would interpret plain-text with
  "HTML-look-alike" characters in them as HTML/Pango
* New modules
    - :py:mod:`.github`: Check Github for pending notifications.
    - :py:mod:`.whosonlocation`: Change your whosonlocation.com status.
    - :py:mod:`.openvpn`: Monitor OpenVPN connections. Currently only supports systems that use Systemd.
    - :py:mod:`.net_speed`: Attempts to provide an estimation of internet speeds.
    - :py:mod:`.makewatch`: Watches for make jobs and notifies when they are completed.
    - :py:mod:`.dota2wins`: Displays the win/loss ratio of a given Dota account.
    - :py:mod:`.dpms`: Shows and toggles status of DPMS which prevents screen from blanking.
    - :py:mod:`.cpu_freq`: uses by default /proc/cpuinfo to determine the current cpu frequency
    - :py:mod:`.updates`: Generic update checker. Currently supports apt-get, pacman and cower
    - :py:mod:`.openstack_vms`: Displays the number of VMs in an openstack
      cluster in ACTIVE and non-ACTIVE states.
* :py:mod:`.backlight`: add xbacklight support for changing brightness with mouse wheel
* :py:mod:`.battery`: added support for depleted batteries
* battery: added support for multiple batteries
* battery: added option to treat all batteries as one large battery (ALL)
* :py:mod:`.cpu_usage`: removed hard coded interval setting
* :py:mod:`.cpu_usage_bar`: fixed wrong default setting
* :py:mod:`.clock`: removed optional pytz dependency
* :py:mod:`.network`: cycle available interfaces on click
* network: centralized network modules
    - Removed ``network_graph``
    - Removed ``network_traffic``
    - Removed ``wireless``
    - All the features of these three modules are now found in network
* network: added total traffic in Mbytes formatters
* network: ``basiciw`` is only required if it is used (wireless)
* network: ``psutil`` is only required if it is used (traffic)
* network: scrolling changes displayed interface
* network: fixed bug that prevented color_up being shown if the user is not using network_traffic
* network: various other enhancements
* :py:mod:`.notmuch`: fixed sync issue with database
* :py:mod:`.now_playing`: added custom format and color when no player is running
* now_playing: differentiates between D-Bus errors and no players running
* now_playing: fixed D-Bus compatibility with players
* :py:mod:`.mail`: added capability to display unread messages per account individually
* :py:mod:`.mpd`: various enhancements and fixes
* :py:mod:`.pulseaudio`: detect default sink changes in pulseaudio
* :py:mod:`.reddit`: can open users mailbox now
* :py:mod:`.shell`: fixed module not stripping newlines
* :py:mod:`.spotify`: check for metadata on start
* :py:mod:`.temp`: alert temperatures
* :py:mod:`.weather`: removed pywapi dependency
* weather: add min_temp and max_temp formatters for daily min/max temperature

3.32 (2014-12-14)
+++++++++++++++++

* Added :py:mod:`.keyboard_locks` module
* Added :py:mod:`.pianobar` module
* Added :py:mod:`.uname` module
* :py:mod:`.cmus`: enhanced artist/title detection from filenames
* cmus: fixed issue when cmus is not running
* :py:mod:`.mpd`: added text_len and truncate_fields options to truncate long artist, album or song names
* :py:mod:`.network_traffic`: added hide_down and format_down options
* :py:mod:`.pomodoro`: added format option
* pomodoro: reset timer on left click
* :py:mod:`.pulseaudio`: fix rounding error of percentage volume

3.31 (2014-10-23)
+++++++++++++++++

* Unexpected exceptions are now displayed in the status bar
* Core: added mouse wheel handling for upcoming i3 version
* Fixed issues with internet-related modules
* New module mixin: ip3ystatus.core.color.ColorRangeModule
* Added :py:mod:`.cmus` module
* Added :py:mod:`.cpu_usage_graph` module
* Added :py:mod:`.network_graph` module
* Added :py:mod:`.network_traffic` module
* Added :py:mod:`.pomodoro` module
* Added :py:mod:`.uptime` module
* :py:mod:`.alsa`: mouse wheel changes volume
* :py:mod:`.battery`: Added no_text_full option
* :py:mod:`.cpu_usage`: Add multicore support
* :py:mod:`.cpu_usage_bar`: Add multicore support
* :py:mod:`.mail`: db_path option made optional
* :py:mod:`.mpd`: Play song on left click even if stopped
* :py:mod:`.network`: Add unknown_up setting
* :py:mod:`.parcel`: Document lxml dependency
* :py:mod:`.pulseaudio`: Added color_muted and color_unmuted options
* pulseaudio: Added step, bar_type, multi_colors, vertical_bar_width options
* pulseaudio: Scroll to change master volume, right click to (un)mute

3.30 (2014-08-04)
+++++++++++++++++

* Added :py:mod:`.bitcoin` module
* Added :py:mod:`.now_playing` module
* Added :py:mod:`.reddit` module
* Added :py:mod:`.shell` module
* Core: fixed custom statusline colors not working properly (see issue #74)
* :py:mod:`.alsa` and :py:mod:`.pulseaudio`: added optional
  "formated_muted" audio is muted.
* :py:mod:`.battery`: add bar formatter, add not_present_text,
  full_color, charging_color, not_present_color settings
* :py:mod:`.disk`: add color and round_size options
* :py:mod:`.maildir`: use os.listdir instead of ls
* :py:mod:`.mem`: add round_size option
* :py:mod:`.mpd`: add color setting
* mpd: add filename formatter
* mpd: next song on right click
* :py:mod:`.network` and wireless: support interfaces enslaved to a
  bonding master
* network: detached_down is now True by default
* network: fixed some issues with interface up/down detection
* :py:mod:`.parcel`: added support for Itella (Finnish national postal
  service) setting. If provided, it will be used instead of "format"
  when the
* :py:mod:`.temp`: add file setting
* temp: fixed issue with Linux kernels 3.15 and newer
* temp: removed color_critical and high_factor options
* :py:mod:`.text`: add cmd_leftclick and cmd_rightclick options
* :py:mod:`.weather`: add colorize option
* :py:mod:`.wireless`: Add quality_bar formatter

3.29 (2014-04-29)
+++++++++++++++++

* :py:mod:`.network`: prefer non link-local v6 addresses
* :py:mod:`.mail`: Open email client and refresh email with mouse click
* :py:mod:`.disk`: Add display and critical limit
* :py:mod:`.battery`: fix errors if CURRENT_NOW is not present
* battery: add configurable colors
* :py:mod:`.load`: add configurable colors and limit
* :py:mod:`.parcel`: rewrote DHL tracker
* Add :py:mod:`.spotify` module

3.28 (2014-04-12)
+++++++++++++++++

* **If you're currently using the i3pystatus command to run your i3bar**:
    Replace ``i3pystatus`` command in your i3 configuration with ``python ~/path/to/your/config.py``
* Do not name your script i3pystatus.py or it will break imports.
* New options for :py:mod:`.mem`
* Added :py:mod:`.cpu_usage`
* Improved error handling
* Removed ``i3pystatus`` binary
* :py:mod:`.pulseaudio:` changed context name to "i3pystatus_pulseaudio"
* Add maildir backend for mails
* Code changes
* Removed DHL tracker of parcel module, because it doesn't work anymore.

3.27 (2013-10-20)
+++++++++++++++++

* Add :py:mod:`.weather` module
* Add :py:mod:`.text` module
* :py:mod:`.pulseaudio`: Add muted/unmuted options

3.26 (2013-10-03)
+++++++++++++++++

* Add :py:mod:`.mem` module

3.24 (2013-08-04)
+++++++++++++++++

**This release introduced changes that may require manual changes to your
configuration file**

* Introduced TimeWrapper
* :py:mod:`.battery`: removed remaining\_* formatters in favor of
  TimeWrapper, as it can not only reproduce all the variants removed,
  but can do much more.
* :py:mod:`.mpd`: Uses TimeWrapper for song_length, song_elapsed


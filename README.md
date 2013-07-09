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


### alsa


Shows volume of ALSA mixer. You can also use this for inputs, btw.

Requires pyalsaaudio


__Settings:__

* `format` — {volume} is the current volume, {muted} is one of `muted` or `unmuted`. {card} is the sound card used; {mixer} the mixer. (default: `♪: {volume}`)
* `mixer` — ALSA mixer (default: `Master`)
* `mixer_id` — ALSA mixer id (default: `0`)
* `card` — ALSA sound card (default: `0`)
* `muted` —  (default: `M`)
* `unmuted` —  (default: ``)
* `color_muted` —  (default: `#AAAAAA`)
* `color` —  (default: `#FFFFFF`)
* `channel` —  (default: `0`)



### backlight


Screen backlight info


__Settings:__

* `format` — format string, formatters: brightness, max_brightness, percentage (default: `{brightness}/{max_brightness}`)
* `backlight` — backlight, see `/sys/class/backlight/` (default: `acpi_video0`)
* `color` —  (default: `#FFFFFF`)



### battery


This class uses the /sys/class/power_supply/…/uevent interface to check for the
battery status

Available formatters for format and alert_format_\*:

* remaining_str
* remaining_hm
* percentage
* percentage_design
* consumption (Watts)
* status
* battery_ident


__Settings:__

* `battery_ident` —  (default: `BAT0`)
* `format` —  (default: `{status} {remaining_hm}`)
* `alert` — Display a libnotify-notification on low battery (default: `False`)
* `alert_percentage` —  (default: `10`)
* `alert_format_title` —  (default: `Low battery`)
* `alert_format_body` —  (default: `Battery {battery_ident} has only {percentage:.2f}% ({remaining_hm}) remaining!`)
* `alert_percentage` —  (default: `10`)
* `path` —  (default: `None`)
* `status` — A dictionary mapping ('DIS', 'CHR', 'FULL') to alternative names (default: `{'FULL': 'FULL', 'CHR': 'CHR', 'DIS': 'DIS'}`)



### clock


This class shows a clock


__Settings:__

* `format` — stftime format string (default: `None`)



### disk


Gets used, free, available and total amount of bytes on the given mounted filesystem.

These values can also be expressed in percentages with the percentage_used, percentage_free
and percentage_avail formats.


__Settings:__

* `format` —  (default: `{free}/{avail}`)
* `path` —  (required)
* `divisor` — divide all byte values by this value, commonly 1024**3 (gigabyte) (default: `1073741824`)



### file


Rip information from text files

components is a dict of pairs of the form:

    name => (callable, file)

* Where `name` is a valid identifier, which is used in the format string to access
the value of that component.
* `callable` is some callable to convert the contents of `file`. A common choice is
float or int.
* `file` names a file, relative to `base_path`.

transforms is a optional dict of callables taking a single argument (a dictionary containing the values
of all components). The return value is bound to the key.


__Settings:__

* `format` —  (required)
* `components` —  (required)
* `transforms` —  (default: `{}`)
* `base_path` —  (default: `/`)
* `color` —  (default: `#FFFFFF`)
* `interval` —  (default: `5`)



### load


Shows system load


__Settings:__

* `format` — format string used for output. {avg1}, {avg5} and {avg15} are the load average of the last one, five and fifteen minutes, respectively. {tasks} is the number of tasks (i.e. 1/285, which indiciates that one out of 285 total tasks is runnable). (default: `{avg1} {avg5}`)



### mail


Generic mail checker

The `backends` setting determines the backends to use. Currently available are:


__Settings:__

* `backends` — List of backends (instances of i3pystatus.mail.xxx)
* `color` —  (default: `#ffffff`)
* `color_unread` —  (default: `#ff0000`)
* `format` —  (default: `{unread} new email`)
* `format_plural` —  (default: `{unread} new emails`)
* `hide_if_null` — Don't output anything if there are no new mails (default: `True`)


    Currently available backends are:


> ### imap
> 
> 
> Checks for mail on a IMAP server
> 
> 
> __Settings:__
> 
> * `host` —  (required)
> * `port` —  (default: `993`)
> * `username` —  (required)
> * `password` —  (required)
> * `ssl` —  (default: `True`)
> 
> 
> 
> ### notmuchmail
> 
> 
> This class uses the notmuch python bindings to check for the
> number of messages in the notmuch database with the tags "inbox"
> and "unread"
> 
> 
> __Settings:__
> 
> * `db_path` —  (required)
> 
> 
> 
> ### thunderbird
> 
> 
> This class listens for dbus signals emitted by
> the dbus-sender extension for thunderbird.
> 
> Requires
> * python-dbus
> 
> 
> __Settings:__
> 
> 
> 
> 
> 

### modsde


This class returns i3status parsable output of the number of
unread posts in any bookmark in the mods.de forums.


__Settings:__

* `format` — Use {unread} as the formatter for number of unread posts (default: `{unread} new posts in bookmarks`)
* `offset` — subtract number of posts before output (default: `0`)
* `color` —  (default: `#7181fe`)
* `username` —  (required)
* `password` —  (required)



### mpd


Displays various information from MPD (the music player daemon)

Available formatters:
* title (the title of the current song)
* album (the album of the current song, can be an empty string (e.g. for online streams))
* artist (can be empty, too)
* playtime_h (Playtime, hours)
* playtime_m (Playtime, minutes)
* playtime_s (Playtime, seconds)
* pos (Position of current song in playlist, one-based)
* len (Length of current playlist)
* status


__Settings:__

* `port` — MPD port (default: `6600`)
* `format` —  (default: `{title} {status}`)
* `status` — Dictionary mapping pause, play and stop to output (default: `{'pause': '▷', 'play': '▶', 'stop': '◾'}`)



### network


Display network information about a interface.

Requires the PyPI package `netifaces-py3`.

Available formatters:
* `{interface}` same as setting
* `{name}` same as setting
* `{v4}` IPv4 address
* `{v4mask}` subnet mask
* `{v4cidr}` IPv4 address in cidr notation (i.e. 192.168.2.204/24)
* `{v6}` IPv6 address
* `{v6mask}` subnet mask
* `{v6cidr}` IPv6 address in cidr notation
* `{mac}` MAC of interface

Not available addresses (i.e. no IPv6 connectivity) are replaced with empty strings.


__Settings:__

* `interface` — Interface to obtain information for (default: `eth0`)
* `format_up` —  (default: `{interface}: {v4}`)
* `color_up` —  (default: `#00FF00`)
* `format_down` —  (default: `{interface}`)
* `color_down` —  (default: `#FF0000`)
* `name` —  (default: `eth0`)



### parcel



__Settings:__

* `instance` — Tracker instance
* `format` —  (default: `{name}:{progress}`)
* `name` 



### pyload


Shows pyLoad status

Available formatters:
* captcha (see captcha_true and captcha_false, which are the values filled in for this formatter)
* progress (average over all running downloads)
* progress_all (percentage of completed files/links in queue)
* speed (kilobytes/s)
* download (downloads enabled, also see download_true and download_false)
* total (number of downloads)
* free_space (free space in download directory in gigabytes)


__Settings:__

* `address` — Address of pyLoad webinterface (default: `http://127.0.0.1:8000`)
* `format` —  (default: `{captcha} {progress_all:.1f}% {speed:.1f} kb/s`)
* `captcha_true` —  (default: `Captcha waiting`)
* `captcha_false` —  (default: ``)
* `download_true` —  (default: `Downloads enabled`)
* `download_false` —  (default: `Downloads disabled`)
* `username` —  (required)
* `password` —  (required)



### regex


Simple regex file watcher


__Settings:__

* `format` — format string used for output (default: `{0}`)
* `regex` —  (required)
* `file` — file to search for regex matches
* `flags` — Python.re flags (default: `0`)



### runwatch


Expands the given path using glob to a pidfile and checks
if the process ID found inside is valid
(that is, if the process is running).
You can use this to check if a specific application, 
such as a VPN client or your DHCP client is running.

Available formatters are {pid} and {name}.


__Settings:__

* `format_up` —  (default: `{name}`)
* `format_down` —  (default: `{name}`)
* `color_up` —  (default: `#00FF00`)
* `color_down` —  (default: `#FF0000`)
* `path` —  (required)
* `name` —  (required)



### temp


Shows CPU temperature of Intel processors

AMD is currently not supported as they can only report a relative temperature, which is pretty useless


__Settings:__

* `format` — format string used for output. {temp} is the temperature in degrees celsius, {critical} and {high} are the trip point temps. (default: `{temp} °C`)
* `color` —  (default: `#FFFFFF`)
* `color_critical` —  (default: `#FF0000`)
* `high_factor` —  (default: `0.7`)



### wireless


Display network information about a interface.

Requires the PyPI packages `netifaces-py3` and `basiciw`.

This is based on the network module, so all options and formatters are
the same, except for these additional formatters:
* {essid} ESSID of currently connected wifi
* {freq} Current frequency
* {quality} Link quality in percent


__Settings:__

* `interface` — Interface to obtain information for (default: `wlan0`)
* `format_up` —  (default: `{interface}: {v4}`)
* `color_up` —  (default: `#00FF00`)
* `format_down` —  (default: `{interface}`)
* `color_down` —  (default: `#FF0000`)
* `name` —  (default: `eth0`)




## Contribute

To contribute a module, make sure it uses one of the Module classes. Most modules
use IntervalModule, which just calls a function repeatedly in a specified interval.

The output attribute should be set to a dictionary which represents your modules output,
the protocol is documented [here](http://i3wm.org/docs/i3bar-protocol.html).

Please add an example for how to configure it to `__main__.py.dist`. It should be
a python class that can be registered with the `I3statusHandler` class. Also don't
forget to add yourself to the LICENSE file.

**Patches and pull requests are very welcome :-)**


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

The config file is just a normal Python module that is executed if you execute
i3pystatus (it is placed inside the i3pystatus package).

You can also execute your config file instead of i3pystatus, but you need to
use an absolute import (`from i3pystatus import Status`) and cannot name it
i3pystatus.py. This is very handy for using different status lines for different
outputs.

A simple configuration file could look like this (note the additional dependencies
from network, wireless and pulseaudio in this example):

    # -*- coding: utf-8 -*-

    import subprocess

    from . import Status

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
        format="{status}/{consumption:.2f}W {percentage:.2f}% [{percentage_design:.2f}%] {remaining_hm}",
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
        format="{status} {remaining_hm}",
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
    # Note: the network module requires PyPI package netifaces-py3
    status.register("network",
        interface="eth0",
        format_up="{v4cidr}",)

    # Has all the options of the normal network and adds some wireless specific things
    # like quality and network names.
    #
    # Note: requires both netifaces-py3 and basiciw
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

    # i3bar
    bar {
        status_command    i3pystatus
        position          top
        workspace_buttons yes
    }

### Formatting

All modules let you specifiy the exact output formatting using a
[format string](http://docs.python.org/3/library/string.html#formatstrings), which
gives you a great deal of flexibility.

Some common stuff:

* If a module gives you a float, it probably has a ton of uninteresting decimal
places. Use `{somefloat:.0f}` to get the integer value, `{somefloat:0.2f}` gives
you two decimal places after the decimal dot

#### formatp

Some modules use an extended format string syntax (the mpd module, for example).
Given the format string below the output adapts itself to the available data.

    [{artist}/{album}/]{title}{status}

Only if both the artist and album is known they're displayed. If only one or none
of them is known the entire group between the brackets is excluded.

"is known" is here defined as "value evaluating to True in Python", i.e. an empty
string or 0 (or 0.0) counts as "not known".

Inside a group always all format specifiers must evaluate to true (logical and).

You can nest groups. The inner group will only become part of the output if both
the outer group and the inner group are eligible for output.

## Modules


### alsa


Shows volume of ALSA mixer. You can also use this for inputs, btw.

Requires pyalsaaudio

Available formatters:

* `{volume}` — the current volume in percent
* `{muted}` — the value of one of the `muted` or `unmuted` settings
* `{card}` — the associated soundcard
* `{mixer}` — the associated ALSA mixer 


__Settings:__

* `format` —  (default: `♪: {volume}`)
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

Available formatters:
* `{brightness}` — current brightness relative to max_brightness
* `{max_brightness}` — maximum brightness value
* `{percentage}` — current brightness in percent


__Settings:__

* `format` — format string, formatters: brightness, max_brightness, percentage (default: `{brightness}/{max_brightness}`)
* `backlight` — backlight, see `/sys/class/backlight/` (default: `acpi_video0`)
* `color` —  (default: `#FFFFFF`)



### battery


This class uses the /sys/class/power_supply/…/uevent interface to check for the
battery status

Available formatters for format and alert_format_\*:

* `{remaining_str}` — remaining time for charging or discharging in the format H:MM
* `{remaining_hm}`- remaining time in the format Hh:MMm
* `{percentage}` — battery percentage relative to the last full value
* `{percentage_design}` — absolute battery charge percentage
* `{consumption (Watts)}` — current power flowing into/out of the battery
* `{status}`
* `{battery_ident}` — the same as the setting


__Settings:__

* `battery_ident` — The name of your battery, usually BAT0 or BAT1 (default: `BAT0`)
* `format` —  (default: `{status} {remaining_hm}`)
* `alert` — Display a libnotify-notification on low battery (default: `False`)
* `alert_percentage` —  (default: `10`)
* `alert_format_title` — The title of the notification, all formatters can be used (default: `Low battery`)
* `alert_format_body` — The body text of the notification, all formatters can be used (default: `Battery {battery_ident} has only {percentage:.2f}% ({remaining_hm}) remaining!`)
* `path` — Override the default-generated path (default: `None`)
* `status` — A dictionary mapping ('DIS', 'CHR', 'FULL') to alternative names (default: `{'FULL': 'FULL', 'DIS': 'DIS', 'CHR': 'CHR'}`)



### clock


This class shows a clock


__Settings:__

* `format` — stftime format string, `None` means to use the default, locale-dependent format (default: `None`)



### disk


Gets `{used}`, `{free}`, `{available}` and `{total}` amount of bytes on the given mounted filesystem.

These values can also be expressed in percentages with the `{percentage_used}`, `{percentage_free}`
and `{percentage_avail}` formats.


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

Available formatters (uses formatp)
* `{title}` — (the title of the current song)
* `{album}` — (the album of the current song, can be an empty string (e.g. for online streams))
* `{artist}` — (can be empty, too)
* `{song_elapsed}` — (Position in the currently playing song, looks like 3:54)
* `{song_length}` — (Length of the current song, same format as song_elapsed)
* `{pos}` — (Position of current song in playlist, one-based)
* `{len}` — (Songs in playlist)
* `{status}` — (play, pause, stop mapped through the `status` dictionary)
* `{bitrate}` — (Current bitrate in kilobit/s)
* `{volume}` — (Volume set in MPD)

Left click on the module play/pauses, right click (un)mutes.


__Settings:__

* `host` —  (default: `localhost`)
* `port` — MPD port (default: `6600`)
* `format` — formatp string (default: `{title} {status}`)
* `status` — Dictionary mapping pause, play and stop to output (default: `{'stop': '◾', 'pause': '▷', 'play': '▶'}`)



### network


Display network information about a interface.

Requires the PyPI package `netifaces-py3`.

Available formatters:
* `{interface}` — same as setting
* `{name}` — same as setting
* `{v4}` — IPv4 address
* `{v4mask}` — subnet mask
* `{v4cidr}` — IPv4 address in cidr notation (i.e. 192.168.2.204/24)
* `{v6}` — IPv6 address
* `{v6mask}` — subnet mask
* `{v6cidr}` — IPv6 address in cidr notation
* `{mac}` — MAC of interface

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



### pulseaudio


Shows volume of default PulseAudio sink (output).

Available formatters:
* `{volume}` — volume in percent (0...100)
* `{db}` — volume in decibels relative to 100 %, i.e. 100 % = 0 dB, 50 % = -18 dB, 0 % = -infinity dB


__Settings:__

* `format` —  (default: `♪: {volume}`)



### pyload


Shows pyLoad status

Available formatters:
* `{captcha}` (see captcha_true and captcha_false, which are the values filled in for this formatter)
* `{progress}` (average over all running downloads)
* `{progress_all}` (percentage of completed files/links in queue)
* `{speed}` (kilobytes/s)
* `{download}` (downloads enabled, also see download_true and download_false)
* `{total}` (number of downloads)
* `{free_space}` (free space in download directory in gigabytes)


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

The groups of the regex are passed to the format string as positional arguments.


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
* `{essid}` — ESSID of currently connected wifi
* `{freq}` — Current frequency
* `{quality}` — Link quality in percent


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

**Patches and pull requests are very welcome :-)**

### The README

The README.md file is generated from the README.tpl.md file; only edit the latter
and run `python -m i3pystatus.mkdocs`.


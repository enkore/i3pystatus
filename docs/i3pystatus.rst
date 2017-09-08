Module reference
================

.. Don't list *every* module here, e.g. cpu-usage suffices, because the other
    variants are listed below that one.

.. rubric:: Module overview:

:System: `clock`_ - `cpu_freq`_ - `cpu_usage`_ - `disk`_ - `keyboard_locks`_ - `load`_ - `mem`_ -
         `swap`_ - `uname`_ - `uptime`_ - `xkblayout`_
:Audio: `alsa`_ - `pulseaudio`_
:Hardware: `backlight`_ - `battery`_ - `temp`_
:Network: `net_speed`_ - `network`_ - `online`_ - `openstack_vms`_ - `openvpn`_
:Music: `cmus`_ - `moc`_ - `mpd`_ - `now_playing`_ - `pianobar`_ - `spotify`_
:Websites: `bitcoin`_ - `dota2wins`_ - `github`_ - `modsde`_ - `parcel`_ - `reddit`_ - `weather`_ -
           `whosonlocation`_
:Other: `anybar`_ - `mail`_ - `pomodoro`_ - `pyload`_ - `text`_ - `updates`_
:Advanced: `file`_ - `regex`_ - `makewatch`_ - `runwatch`_ - `shell`_

.. autogen:: i3pystatus Module

   .. rubric:: Module list:

.. _mailbackends:

Mail Backends
-------------

The generic mail module can be configured to use multiple mail backends. Here is an
example configuration for the MaildirMail backend:

.. code:: python

    from i3pystatus.mail import maildir
    status.register("mail",
                    backends=[maildir.MaildirMail(
                            directory="/home/name/Mail/inbox")
                    ],
                    format="P {unread}",
                    log_level=20,
                    hide_if_null=False, )

.. autogen:: i3pystatus.mail SettingsBase

   .. nothin'

.. _scorebackends:

Score Backends
--------------

.. autogen:: i3pystatus.scores SettingsBase

    .. nothin'

.. _updatebackends:

Update Backends
---------------

.. autogen:: i3pystatus.updates SettingsBase

    .. nothin'

.. _weatherbackends:

Weather Backends
----------------

.. autogen:: i3pystatus.weather SettingsBase

    .. nothin'

.. calendarbackends:

Calendar Backends
-----------------

Generic calendar interface. Requires the PyPI package ``colour``.

.. rubric:: Available formatters

* {title} - the title or summary of the event
* {remaining_time} - how long until this event is due

Additional formatters may be provided by the backend, consult their documentation for details.

.. rubric:: Settings

* {update_interval} - how often (in seconds) the calendar backend should be called to update events
* {dynamic_color} - when set, the color shifts as the event approaches
* {urgent_blink} - when set, urgent is toggled every second when within urgent_seconds of the event
* {urgent_seconds} - how many seconds before the event to begin blinking
* {skip_recurring} - when set, recurring events are skipped

Here is an example of configuring the calendar module to use the ``Lightning`` backend:

.. code:: python

    status.register("calendar",
                format="{title} {remaining}",
                update_interval=10,
                urgent_blink=True,
                backend=Lightning(database_path=path, days=2))

.. autogen:: i3pystatus.calendar SettingsBase

    .. nothin'
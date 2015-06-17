Configuration
=============

The configuration file is a normal Python script. The status bar is controlled by a central
:py:class:`.Status` object, which individual *modules* like a :py:mod:`.clock` or a :py:mod:`.battery`
monitor are added to with the ``register`` method.

A typical configuration file could look like this (note the additional
dependencies from :py:mod:`.network` and :py:mod:`.pulseaudio` in this
example):

.. code:: python

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
    # This would also display a desktop notification (via D-Bus) if the percentage
    # goes below 5 percent while discharging. The block will also color RED.
    # If you don't have a desktop notification demon yet, take a look at dunst:
    #   http://www.knopwob.org/dunst/
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

    # Note: requires both netifaces and basiciw (for essid and quality)
    status.register("network",
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

.. code:: ini

    # i3bar
    bar {
        status_command    python ~/.path/to/your/config/file.py
        position          top
        workspace_buttons yes
    }

.. note:: Don't name your config file ``i3pystatus.py``, as it would
    make ``i3pystatus`` un-importable and lead to errors.

Credentials
-----------

Settings that require credentials can utilize the keyring module to
keep sensitive information out of config files.  To take advantage of
this feature, simply use the ``i3pystatus-setting-util`` script
installed along i3pystatus to set the credentials for a module. Once
this is done you can add the module to your config without specifying
the credentials, e.g.:

.. code:: python

    # Use the default keyring to retrieve credentials.
    # To determine which backend is the default on your system, run
    # python -c 'import keyring; print(keyring.get_keyring())'
    status.register('github')

If you don't want to use the default you can set a specific keyring like so:

.. code:: python

    from keyring.backends.file import PlaintextKeyring
    status.register('github', keyring_backend=PlaintextKeyring())

i3pystatus will locate and set the credentials during the module
loading process. Currently supported credentials are "password",
"email" and "username".

.. note:: Credential handling requires the PyPI package
   ``keyring``. Many distributions have it pre-packaged available as
   ``python-keyring``.

Formatting
----------

All modules let you specifiy the exact output formatting using a
`format string <http://docs.python.org/3/library/string.html#formatstrings>`_, which
gives you a great deal of flexibility.

If a module gives you a float, it probably has a ton of
uninteresting decimal places. Use ``{somefloat:.0f}`` to get the integer
value, ``{somefloat:0.2f}`` gives you two decimal places after the
decimal dot

.. _formatp:

formatp
~~~~~~~

Some modules use an extended format string syntax (the :py:mod:`.mpd`
module, for example).  Given the format string below the output adapts
itself to the available data.

::

    [{artist}/{album}/]{title}{status}

Only if both the artist and album is known they're displayed. If only one or none
of them is known the entire group between the brackets is excluded.

"is known" is here defined as "value evaluating to True in Python", i.e. an empty
string or 0 (or 0.0) counts as "not known".

Inside a group always all format specifiers must evaluate to true (logical and).

You can nest groups. The inner group will only become part of the output if both
the outer group and the inner group are eligible for output.

.. _TimeWrapper:

TimeWrapper
~~~~~~~~~~~

Some modules that output times use :py:class:`.TimeWrapper` to format
these. TimeWrapper is a mere extension of the standard formatting
method.

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

Logging
-------

Errors do happen and to ease debugging i3pystatus includes a logging
facility.  By default i3pystatus will log exceptions raised by modules
to files in your home directory named
``.i3pystatus-<pid-of-thread>``. Some modules might log additional
information.

.. rubric:: Log level

Every module has a ``log_level`` option which sets the *minimum*
severity required for an event to be logged.

The numeric values of logging levels are given in the following
table.

+--------------+---------------+
| Level        | Numeric value |
+==============+===============+
| ``CRITICAL`` | 50            |
+--------------+---------------+
| ``ERROR``    | 40            |
+--------------+---------------+
| ``WARNING``  | 30            |
+--------------+---------------+
| ``INFO``     | 20            |
+--------------+---------------+
| ``DEBUG``    | 10            |
+--------------+---------------+
| ``NOTSET``   | 0             |
+--------------+---------------+

Exceptions raised by modules are of severity ``ERROR`` by default. The
default ``log_level`` in i3pystatus (some modules might redefine the
default, see the reference of the module in question) is 30
(``WARNING``).

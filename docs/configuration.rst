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

    status = Status()

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

Another way to launch your configuration file is to use ``i3pystatus`` script
from installation:

.. code:: bash

    i3pystatus -c ~/.path/to/your/config/file.py

If no arguments were provided, ``i3pystatus`` script works as an example of
``Clock`` module.

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

Some modules use an extended format string syntax (the :py:mod:`.mpd` and
:py:mod:`.weather` modules, for example). Given the format string below the
output adapts itself to the available data.

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

.. _logging:

Logging
-------

Errors do happen and to ease debugging i3pystatus includes a logging
facility.  By default i3pystatus will log exceptions raised by modules
to files in your home directory named
``.i3pystatus-<pid-of-thread>``. Some modules might log additional
information.

Setting a specific logfile
~~~~~~~~~~~~~~~~~~~~~~~~~~

When instantiating your ``Status`` object, the path to a log file can be
specified (it accepts environment variables). If this is done, then log messages will be sent to that file and not
to an ``.i3pystatus-<pid-of-thread>`` file in your home directory.  This is
useful in that it helps keep your home directory from becoming cluttered with
files containing errors.

.. code-block:: python

    from i3pystatus import Status

    status = Status(logfile='$HOME/var/i3pystatus.log')

Changing log format
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 3.35

The ``logformat`` option can be useed to change the format of the log files,
using `LogRecord attributes`__.

.. code-block:: python

    from i3pystatus import Status

    status = Status(
        logfile='/home/username/var/i3pystatus.log',
        logformat='%(asctime)s %(levelname)s:',
    )

.. __: https://docs.python.org/3/library/logging.html#logrecord-attributes


Log level
~~~~~~~~~

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

.. _callbacks:

Callbacks
---------

Callbacks are used for click-events (merged into i3bar since i3 4.6,
mouse wheel events are merged since 4.8), that is, you click (or
scroll) on the output of a module in your i3bar and something
happens. What happens is defined by these settings for each module
individually:

- ``on_leftclick``
- ``on_doubleleftclick``
- ``on_rightclick``
- ``on_doublerightclick``
- ``on_upscroll``
- ``on_downscroll``

The global default action for all settings is ``None`` (do nothing),
but many modules define other defaults, which are documented in the
module reference.

.. note::
    Each of these callbacks, when triggered, will call the module's ``run()``
    function (typically only called each time the module's interval is
    reached). If there are things in the ``run()`` function of your module
    which you do not want to be executed every time a mouse event is triggered,
    then consider using threading to perform the module update, and manually
    sleep for the module's interval between updates. You can start the update
    thread in the module's ``init()`` function. The ``run()`` function can then
    either just update the module's displayed text, or simply do nothing (if
    your update thread also handles updating the display text). See the
    `weather module`_ for an example of this method.

    .. _`weather module`: https://github.com/enkore/i3pystatus/blob/82fc9fb/i3pystatus/weather/__init__.py#L244-L265

The values you can assign to these four settings can be divided to following
three categories:

.. rubric:: Member callbacks

These callbacks are part of the module itself and usually do some simple module
related tasks (like changing volume when scrolling, etc.). All available
callbacks are (most likely not) documented in their respective module
documentation.

For example the module :py:class:`.ALSA` has callbacks named ``switch_mute``,
``increase_volume`` and ``decrease volume``. They are already assigned by
default but you can change them to your liking when registering the module.

.. code:: python

    status.register("alsa",
        on_leftclick = ["switch_mute"],
        # or as a strings without the list
        on_upscroll = "decrease_volume",
        on_downscroll = "increase_volume",
        # this will refresh any module by clicking on it
        on_rightclick = "run",
        )

Some callbacks also have additional parameters. Both ``increase_volume`` and
``decrease_volume`` have an optional parameter ``delta`` which determines the
amount of percent to add/subtract from the current volume.

.. code:: python

    status.register("alsa",
        # all additional items in the list are sent to the callback as arguments
        on_upscroll = ["decrease_volume", 2],
        on_downscroll = ["increase_volume", 2],
        )


.. rubric:: Python callbacks

These refer to to any callable Python object (most likely a
function). To external Python callbacks that are not part of the
module the ``self`` parameter is not passed by default. This allows to
use many library functions with no additional wrapper.

If ``self`` is needed to access the calling module, the
:py:func:`.get_module` decorator can be used on the callback:

.. code:: python

    from i3pystatus import get_module

    # Note that the 'self' parameter is required and gives access to all
    # variables of the module.
    @get_module
    def change_text(self):
        self.output["full_text"] = "Clicked"

    status.register("text",
        text = "Initial text",
        on_leftclick = [change_text],
        # or
        on_rightclick = change_text,
        )

If the module your attaching the callback too is not a subclass of
:py:class:`.IntervalModule` you will need to invoke ``init()``.
using :py:class:`.Uname` as an example, the following code would suffice.

.. code:: python

    from i3pystatus import get_module

    @get_module
    def sys_info(self):
        if self.format == "{nodename}":
                self.format = "{sysname} {release} on {machine}"
            else:
                self.format = "{nodename}"
            self.init()

    status.register("uname", format="{nodename}", on_rightclick=sys_info)

You can also create callbacks with parameters.

.. code:: python

    from i3pystatus import get_module

    @get_module
    def change_text(self, text="Hello world!", color="#ffffff"):
        self.output["full_text"] = text
        self.output["color"] = color

    status.register("text",
        text = "Initial text",
        color = "#00ff00",
        on_leftclick = [change_text, "Clicked LMB", "#ff0000"],
        on_rightclick = [change_text, "Clicked RMB"],
        on_upscroll = change_text,
        )

.. rubric:: External program callbacks

You can also use callbacks to execute external programs. Any string that does
not match any `member callback` is treated as an external command. If you want
to do anything more complex than executing a program with a few arguments,
consider creating an `python callback` or execute a script instead.

.. code:: python

    status.register("text",
        text = "Launcher?",
        # open terminal window running htop
        on_leftclick = "i3-sensible-terminal -e htop",
        # open i3pystatus github page in firefox
        on_rightclick = "firefox --new-window https://github.com/enkore/i3pystatus",
        )

Most modules provide all the formatter data to program callbacks. The snippet below
demonstrates how this could be used, in this case XMessage will display a dialog box
showing verbose information about the network interface:

.. code:: python

    status.register("network",
        interface="eth0",
        on_leftclick="ip addr show dev {interface} | xmessage -file -"
        )


.. _hints:

Hints
-----

Hints are additional parameters used to customize output of a module.
They give you access to all attributes supported by `i3bar protocol
<http://i3wm.org/docs/i3bar-protocol.html#_blocks_in_detail>`_.

Hints are available as the ``hints`` setting in all modules and its
value should be a dictionary or ``None``. An attribute defined in
``hints`` will be applied only if the module output does not contain
attribute with the same name already.

Some possible uses for these attributes are:

*   `min_width` and `align` can be used to set minimal width of output and
    align the text if its width is shorter than `minimal_width`.
*   `separator` and `separator_block_width` can be used to remove the
    vertical bar that is separating modules.
*   `background` can be used to set an alternative background color for the
    module. supports RGBA if your i3bar version does.
*   `markup` can be set to `"none"` or `"pango"`.
    `Pango markup
    <https://developer.gnome.org/pango/stable/PangoMarkupFormat.html>`_
    provides additional formatting options for drawing rainbows and other
    fancy stuff.

.. note:: Pango markup requires that i3bar is configured to use `Pango <http://i3wm.org/docs/userguide.html#fonts>`_, too. It can't work with X core fonts.

Here is an example with the :py:mod:`.network` module.
Pango markup is used to keep the ESSID green at all times while the
recieved/sent part is changing color depending on the amount of traffic.

  .. code:: python

        status.register("network",
            interface = "wlp2s0",
            hints = {"markup": "pango"},
            format_up = "<span color=\"#00FF00\">{essid}</span> {bytes_recv:6.1f}KiB {bytes_sent:5.1f}KiB",
            format_down = "",
            dynamic_color = True,
            start_color = "#00FF00",
            end_color = "#FF0000",
            color_down = "#FF0000",
            upper_limit = 800.0,
            )

Or you can use pango to customize the color of ``status`` setting in
:py:mod:`.now_playing` and :py:mod:`.mpd` modules.

    .. code:: python

        ...
        hints = {"markup": "pango"},
        status = {
            "play": "▶",
            "pause": "<span color=\"orange\">▶</span>",
            "stop": "<span color=\"red\">◾</span>",
        },
        ...

Or make two modules look like one.

    .. code:: python

        status.register("text",
            text = "shmentarianism is a pretty long word.")
        status.register("text",
            hints = {"separator": False, "separator_block_width": 0},
            text = "Antidisestabli",
            color="#FF0000")

.. _refresh:

Refreshing the bar
------------------

The whole bar can be refreshed by sending SIGUSR1 signal to i3pystatus
process.  This feature is not available in chained mode
(:py:class:`.Status` was created with ``standalone=False`` parameter
and gets it's input from ``i3status`` or a similar program).

To find the PID of the i3pystatus process look for the ``status_command`` you
use in your i3 config file.
If your `bar` section of i3 config looks like this

    .. code::

        bar {
            status_command python ~/.config/i3/pystatus.py
        }

then you can refresh the bar by using the following command:

    .. code:: bash

        pkill -SIGUSR1 -f "python /home/user/.config/i3/pystatus.py"

Note that the path must be expanded if using '~'.

.. _internet:

Internet Connectivity
---------------------

Module methods that ``@require(internet)`` won't be run unless a test TCP
connection is successful. By default, this is made to Google's DNS server, but
you can customize the host and port. See :py:class:`.internet`.

If you are behind a gateway that redirects web traffic to an authorization page
and blocks other traffic, the DNS check will return a false positive. This is
often encountered in open WiFi networks. In these cases it is helpful to try a
service that is not traditionally required for web browsing:

.. code:: python

  from i3pystatus import Status

  status = Status(check_internet=("whois.arin.net", 43))

.. code:: python

  from i3pystatus import Status

  status = Status(check_internet=("github.com", 22))

.. _credentials:

Credentials
-----------

For modules which require credentials, i3pystatus supports credential
management using the keyring_ module from PyPI.

.. important::
    Many distributions have keyring_ pre-packaged, available as
    ``python-keyring``. Unless you have KWallet_ or SecretService_ available,
    you will also most likely need to install keyrings.alt_, which contains
    additional keyring backends for use by the keyring_ module.

    Both i3pystatus and ``i3pystatus-setting-util`` will abort with a
    RuntimeError_ if keyring_ isinstalled but a usable keyring backend is not
    present, so it is a good idea to install both if you plan to use a module
    which supports credential handling.

To store credentials in a keyring, use the ``i3pystatus-setting-util`` script
installed along i3pystatus.

.. note::
    ``i3pystatus-setting-util`` will store credentials using the default
    keyring backend. The method for determining which backend is the default
    can be found :ref:`below <default-keyring-backend>`. If, for some reason,
    it is necessary to use a keyring other than the default, then you will need
    to override the default in your keyringrc.cfg_ for
    ``i3pystatus-setting-util`` to successfully use it.

Once you have successfully set up credentials, you can add the module to your
config file without specifying the credentials in the registration, e.g.:

.. code:: python

    # Use the default keyring to retrieve credentials
    status.register('github')

i3pystatus will locate and set the credentials during the module loading
process. Currently supported credentials are ``password``, ``email`` and
``username``.

.. _default-keyring-backend:

.. note::
    To determine which backend is the default on your system, run the
    following:

    .. code-block:: bash

        python -c 'import keyring; print(keyring.get_keyring())'

    If this command returns a ``keyring.backends.fail.Keyring`` object, none of
    the keyrings supported out-of-the box by the keyring_ module are available,
    and you will need to install the keyrings.alt_ Python module. keyrings.alt_
    provides an encrypted keyring which will be seen as the default if both
    keyrings.alt_ and keyring_ are installed, and none of the keyrings
    supported by keyring_ are present:

    .. code-block:: bash

        $ python -c 'import keyring; print(keyring.get_keyring())'
        <EncryptedKeyring at /home/username/.local/share/python_keyring/crypted_pass.cfg>

If the keyring backend you used to store credentials using
``i3pystatus-setting-util`` is not the default, then you can change which
keyring backend i3pystatus will use in one of two ways:

#. Override the default in your keyringrc.cfg_

#. Import and instantiate a keyring backend class, and pass it as the
   ``keyring_backend`` parameter when registering the module:

   .. code:: python

       # Requires the keyrings.alt package
       from keyrings.alt.file import PlaintextKeyring
       status.register('github', keyring_backend=PlaintextKeyring())

.. _KWallet: http://www.kde.org/
.. _SecretService: https://specifications.freedesktop.org/secret-service/re01.html
.. _RuntimeError: https://docs.python.org/3/library/exceptions.html#RuntimeError
.. _keyring: https://pypi.python.org/pypi/keyring
.. _keyrings.alt: https://pypi.python.org/pypi/keyrings.alt
.. _keyringrc.cfg: http://pythonhosted.org/keyring/#customize-your-keyring-by-config-file

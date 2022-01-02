Installation
============

.. rubric:: Supported Python Versions

i3pystatus requires Python 3.6 or newer and is not compatible with Python 2.
Some modules require additional dependencies documented in the docs.

Into Virtualenv
---------------

i3pystatus no longer uses numbered releases. Therefore, the recommended method
is to install from git via ``pip``, and into a virtualenv to avoid polluting
your site-packages directory.

First, create a virtualenv:

.. code-block:: bash

    $ python3 -mvenv /path/to/virtualenv

Next, activate into the virtualenv and use pip to install i3pystatus into it:

.. code-block:: bash

    $ source /path/to/virtualenv/bin/activate
    $ pip install git+https://github.com/enkore/i3pystatus.git

If you are installing for development, use ``pip install --editable`` instead:

.. code-block:: bash

    $ source /path/to/virtualenv/bin/activate
    $ pip install --editable /path/to/clone/of/i3pystatus

**NOTE:** If you need to install any additional dependencies required by the
i3pystatus modules you are using, you will also need to install them into this
virtualenv.

Invoking From Virtualenv
------------------------

To invoke i3pystatus from your virtualenv, use the ``python`` symlink from the
virtualenv to run your i3pystatus config script. See the following example
``bar`` section from ``~/.config/i3/config``:

.. code-block:: text

    bar {
        colors {
             statusline #949494
             separator #4e4e4e
        }
        separator_symbol "|"
        position top
        status_command /path/to/virtualenv/bin/python /home/username/.config/i3/status.py
    }

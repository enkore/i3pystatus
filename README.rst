i3pystatus
==========

.. image:: http://golem.enkore.de/job/i3pystatus-dev/badge/icon
    :target: http://golem.enkore.de/job/i3pystatus-dev/

.. image:: https://travis-ci.org/enkore/i3pystatus.svg?branch=master
    :target: https://travis-ci.org/enkore/i3pystatus

i3pystatus is a growing collection of python scripts for
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

`All further user documentation has been moved here. <http://docs.enkore.de/i3pystatus>`_

Changelog
---------

`Located here. <http://docs.enkore.de/i3pystatus/changelog.html>`_

Contributors
------------

A list of all contributors can be found in `CONTRIBUTORS <https://github.com/enkore/i3pystatus/blob/master/CONTRIBUTORS>`_.
Particular noteworthy contributors are former maintainer Jan Oliver Oelerich and
current maintainer enkore.

Contribute
----------

To contribute a module, make sure it uses one of the ``Module`` classes. Most modules
use ``IntervalModule``, which just calls a function repeatedly in a specified interval.

The ``output`` attribute should be set to a dictionary which represents your modules output,
the protocol is documented `here <http://i3wm.org/docs/i3bar-protocol.html>`_.

Developer documentation is available in the source code and `here
<http://docs.enkore.de/i3pystatus>`_.

**Patches and pull requests are very welcome :-)**

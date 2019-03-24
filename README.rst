i3pystatus
==========

.. image:: https://travis-ci.org/enkore/i3pystatus.svg?branch=master
    :target: https://travis-ci.org/enkore/i3pystatus

i3pystatus is a large collection of status modules compatible with i3bar from the i3 window manager.

:License: MIT
:Python: 3.5+
:Governance: Patches that don't break the build (Travis or docs) are generally just merged. This is a "do-it-yourself" project, so to speak.
:Releases: No further releases are planned. Install it from Git.

Installation
------------

**Supported Python versions**
    i3pystatus requires Python 3.5 or newer and is not compatible with
    Python 2.x. Some modules require additional dependencies
    documented in the docs.

::

    pip3 install git+https://github.com/enkore/i3pystatus.git

Documentation
-------------

`All further user documentation has been moved here. <https://i3pystatus.readthedocs.io/>`_

The changelog for old releases can be found `here. <https://i3pystatus.readthedocs.io/en/latest/changelog.html>`_

Contributors
------------

A list of all contributors can be found in `CONTRIBUTORS <https://github.com/enkore/i3pystatus/blob/master/CONTRIBUTORS>`_, but git likely has more up-to-date information. i3pystatus was initially written by Jan Oliver Oelerich and later ported to Python 3 and mostly rewritten by enkore.

Contribute
----------

To contribute a module, make sure it uses one of the ``Module`` classes. Most modules
use ``IntervalModule``, which just calls a function repeatedly in a specified interval.

The ``output`` attribute should be set to a dictionary which represents your modules output,
the protocol is documented `here <http://i3wm.org/docs/i3bar-protocol.html>`_.

Developer documentation is available in the source code and `here
<https://i3pystatus.readthedocs.io/en/latest/module.html>`_.

**Patches and pull requests are very welcome :-)**

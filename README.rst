i3pystatus
==========

.. image:: http://golem.enkore.de/job/i3pystatus-dev/badge/icon
    :target: http://golem.enkore.de/job/i3pystatus-dev/

.. image:: https://travis-ci.org/enkore/i3pystatus.svg?branch=master
    :target: https://travis-ci.org/enkore/i3pystatus

i3pystatus is a large collection of status modules compatible with i3bar from the i3 window manager.

:License: MIT
:Python: 3.4+
:Governance: Patches that don't break the build (Travis or docs) are generally just merged.
:Releases: No further releases are planned. Install it from Git.

Installation
------------

**Supported Python versions**
    i3pystatus requires Python 3.4 or newer and is not compatible with
    Python 2.x. Some modules require additional dependencies
    documented in the docs.

::

    pip3 install git+https://github.com/enkore/i3pystatus.git

Documentation
-------------

`All further user documentation has been moved here. <https://i3pystatus.readthedocs.io/>`_

Changelog
---------

`Located here. <https://i3pystatus.readthedocs.io/en/latest/changelog.html>`_ Note: no further releases are planned. Install it from Git.

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
<https://i3pystatus.readthedocs.io/en/latest/module.html>`_.

**Patches and pull requests are very welcome :-)**

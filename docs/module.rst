
Creating modules
================

Creating new modules ("things that display something") to contribute
to i3pystatus is reasonably easy. If the module you want to write
updates it's info periodically, like checking for a network link or
displaying the status of some service, then we have prepared common
tools for this which make this even easier:

- Common base classes: :py:class:`.Module` for everything and
  :py:class:`.IntervalModule` specifically for the aforementioned
  usecase of updating stuff periodically.

  the :py:class:`.Module` class inherits a `logger` attribute and as such
  all logging should be implemented via `self.logger.<level>` rather then
  initializing a new logger in the module.

- Settings (already built into above classes) allow you to easily
  specify user-modifiable attributes of your class for configuration.

  See :py:class:`.SettingsBase` for details.
- For modules that require credentials, it is recommended to add a
  keyring_backend setting to allow users to specify their own backends
  for retrieving sensitive credentials.

  Required settings and default values are also handled.

Check out i3pystatus' source code for plenty of (`simple
<https://github.com/enkore/i3pystatus/blob/master/i3pystatus/mem.py>`_)
examples on how to build modules.

The settings system is built to ease documentation. If you specify
two-tuples like ``("setting", "description")`` then Sphinx will
automatically generate a nice table listing each option, it's default
value and description.

The docstring of your module class is automatically used as the
reStructuredText description for your module in the README file.

.. seealso::

    :py:class:`.SettingsBase` for a detailed description of the settings system

Handling Dependencies
---------------------

To make it as easy as possible to use i3pystatus we explicitly
document all dependencies in the docstring of a module.

The wording usually used goes like this:

.. code:: rst

   Requires the PyPI package `colour`

To allow automatic generation of the docs without having all
requirements of every module installed mocks are used. To make this
work simply add all modules of dependencies (so no standard library modules
or modules provided by i3pystatus) you import to the ``MOCK_MODULES``
list in ``docs/conf.py``. This needs to be the actual name of the imported
module, so for example if you have ``from somepkg.mod import AClass``,
you need to add ``somepkg.mod`` to the list.

Testing changes
---------------

i3pystatus uses continuous integration (CI) techniques, which means in
our case that every patch and every pull request is tested
automatically. While Travis is used for automatic building of GitHub
pull requests, it is not the authoritative CI system (which is `Der Golem
<http://golem.enkore.de/>`_) for the main repository.

The ``ci-build.sh`` script needs to run successfully for a patch to be
accepted. It can be run on your machine, too, so you don't need to
wait for the often slow Travis build to complete. It does not require
any special privileges, except write access to the ``ci-build``
directory (a different build directory can be specified as the first
parameter to ``ci-build.sh``).

The script tests the following things:

1. PEP8 compliance of the entire codebase, *excluding* errors of too
   long lines (error code E501). Line lengths of about 120 characters
   are acceptable.
2. That ``setup.py`` installs i3pystatus and related binaries (into a
   location below the build directory)
3. Unit tests pass, they are tested against the installed version from
   2.). A unit test log in JUnit format is generated in the build
   directory (``testlog.xml``).
4. Sphinx docs build without errors or warnings. The HTML docs are
   generated in the ``docs`` directory in the build directory.

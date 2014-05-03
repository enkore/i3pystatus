
Creating modules
================

Creating new modules ("things that display something") to contribute
to i3pystatus is reasonably easy. If the module you want to write
updates it's info periodically, like checking for a network link or
displaying the status of some service, then we have prepared common
tools for this which make this even easier:

- Common base classes: :py:class:`i3pystatus.core.modules.Module` for
  everything and :py:class:`i3pystatus.core.modules.IntervalModule`
  specifically for the aforementioned usecase of updating stuff
  periodically.
- Settings (already built into above classes) allow you to easily
  specify user-modifiable attributes of your class for configuration.

  Required settings and default values are also handled.

Check out i3pystatus' source code for plenty of (`simple
<https://github.com/enkore/i3pystatus/blob/master/i3pystatus/mem.py>`_)
examples on how to build modules.

Also note that the settings system is built to ease documentation. If
you specify two-tuples ``("setting", "description")`` description then
:py:mod:`i3pystatus.mkdocs` will automatically generate a nice table
listing each option, it's default value and description.

The docstring of your module class is automatically used as the
restructuredtext description for your module in the README file.

.. seealso::

    :py:class:`i3pystatus.core.settings.SettingsBase` for a detailed description of the settings system

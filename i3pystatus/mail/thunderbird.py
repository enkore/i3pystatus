# This plugin listens for dbus signals emitted by the
# thunderbird-dbus-sender extension for TB:
# https://github.com/janoliver/thunderbird-dbus-sender
# The plugin must be active and thunderbird running for the module to work
# properly.

from functools import partial

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject

from i3pystatus.mail import Backend


class Thunderbird(Backend):
    """
    This class listens for dbus signals emitted by
    the dbus-sender extension for thunderbird.

    Requires python-dbus
    """

    _unread = set()

    def init(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        bus.add_signal_receiver(self.new_msg,
                                dbus_interface="org.mozilla.thunderbird.DBus",
                                signal_name="NewMessageSignal")
        bus.add_signal_receiver(self.changed_msg,
                                dbus_interface="org.mozilla.thunderbird.DBus",
                                signal_name="ChangedMessageSignal")
        loop = GObject.MainLoop()
        dbus.mainloop.glib.threads_init()
        self.context = loop.get_context()

        self.run = partial(self.context.iteration, False)

    def new_msg(self, id, author, subject):
        if id not in self._unread:
            self._unread.add(id)

    def changed_msg(self, id, event):
        if event == "read" and id in self._unread:
            self._unread.remove(id)

    @property
    def unread(self):
        self.run()
        return len(self._unread)


Backend = Thunderbird

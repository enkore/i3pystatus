#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This plugin listens for dbus signals emitted by the 
# thunderbird-dbus-sender extension for TB: 
# https://github.com/janoliver/thunderbird-dbus-sender
# The plugin must be active and thunderbird running for the module to work
# properly.

import dbus, gobject
from dbus.mainloop.glib import DBusGMainLoop
import json
import threading
import time

class ThunderbirdMailChecker(object):
    """ 
    This class listens for dbus signals emitted by
    the dbus-sender extension for thunderbird. 
    """

    async = True
    output = None

    unread = set()

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        bus.add_signal_receiver(self.new_msg,
                                dbus_interface="org.mozilla.thunderbird.DBus",
                                signal_name="NewMessageSignal")
        bus.add_signal_receiver(self.changed_msg,
                                dbus_interface="org.mozilla.thunderbird.DBus",
                                signal_name="ChangedMessageSignal")
        loop = gobject.MainLoop()
        dbus.mainloop.glib.threads_init()
        self.context = loop.get_context()

        self.thread = threading.Thread(target=self.mainloop)
        self.thread.daemon = True
        self.thread.start()

    def mainloop(self):
        while True:
            self.context.iteration(False)
            time.sleep(1)

    def new_msg(self, id, author, subject):
        if id not in self.unread:
            self.unread.add(id)
            self._output()

    def changed_msg(self, id, event):
        if event == "read" and id in self.unread:
            self.unread.remove(id)
            self._output()

    def _output(self):
        self.context.iteration(False)

        unread = len(self.unread)
        if unread:
            self.output = {'full_text' : '%d new email' % unread, 
                'name' : 'newmail-tb',
                'urgent' : True,
                'color' : '#ff0000' }
        else:
            self.output = None


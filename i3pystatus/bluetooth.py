from os.path import basename

import dbus

from i3pystatus import IntervalModule, formatp
from i3pystatus.core.util import TimeWrapper

def proxyobj(bus, path, interface):
    """ commodity to apply an interface to a proxy object """
    obj = bus.get_object('org.bluez', path)
    return dbus.Interface(obj, interface)


def filter_by_interface(objects, interface_name):
    """ filters the objects based on their support
        for the specified interface """
    result = []
    for path in objects.keys():
        interfaces = objects[path]
        for interface in interfaces.keys():
            if interface == interface_name:
                result.append(path)
    return result

def get_bluetooth_device_list():
    # shamelessly stolen from https://stackoverflow.com/questions/14262315/list-nearby-discoverable-bluetooth-devices-including-already-paired-in-python/14267310#14267310
    bus = dbus.SystemBus()

    # we need a dbus object manager
    manager = proxyobj(bus, "/", "org.freedesktop.DBus.ObjectManager")
    objects = manager.GetManagedObjects()

    # once we get the objects we have to pick the bluetooth devices.
    # They support the org.bluez.Device1 interface
    devices = filter_by_interface(objects, "org.bluez.Device1")

    # now we are ready to get the informations we need
    bt_devices = []
    for device in devices:
        obj = proxyobj(bus, device, 'org.freedesktop.DBus.Properties')
        bt_devices.append({
            "name": str(obj.Get("org.bluez.Device1", "Name")),
            "dev_addr": str(obj.Get("org.bluez.Device1", "Address"))
        })
    return bt_devices

class Bluetooth(IntervalModule):
    """
    Shows currently connected bluetooth devices. 

        * Requires ``python-dbus`` from your distro package manager, or \
``dbus-python`` from PyPI.

        Left click on the module to cycle forwards through devices, and right \
click to cycle backwards.

        .. rubric:: Available formatters (uses :ref:`formatp`)

        * `{name}` — (the name of the device)
        * `{dev_addr}` — (the bluetooth device address)
        
        .. rubric:: Available callbacks

        * ``next_device`` — iterate forward through devices
        * ``prev_device`` — iterate backwards through devices

        Example module registration with callbacks:

        ::
            status.register("now_playing",
                on_leftclick="next_device",
                on_rightclick="prev_device",
                on_upscroll="next_device",
                on_downscroll="prev_device")
    """

    interval = 1

    settings = (
        ("format", "formatp string"),
        ("color", "Text color"),
    )

    format = "{name}:{dev_addr}"
    color = "#ffffff"
    
    on_leftclick = "next_device"
    on_rightclick = "prev_device"
    on_upscroll = 'next_device'
    on_downscroll = 'prev_device'

    num_devices = 0
    dev_index = 0
    devices = []


    def run(self):
        try:
            self.devices = get_bluetooth_device_list()
            self.dev_index = self.dev_index % len(self.devices)
            self.num_devices = len(self.devices)

            if len(self.devices) < 1:
                if hasattr(self, "data"):
                    del self.data
                self.output = None
                return

            fdict = {
                "name": self.devices[self.dev_index]['name'],
                "dev_addr": self.devices[self.dev_index]['dev_addr']
            }

            self.data = fdict
            self.output = {
                "full_text": formatp(self.format, **fdict).strip(),
                "color": self.color,
            }
            return
        except dbus.exceptions.DBusException as e:
            self.output = {
                "full_text": "DBus error: " + e.get_dbus_message(),
                "color": "#ff0000",
            }
            if hasattr(self, "data"):
                del self.data
            return

    def next_device(self):
        self.dev_index = (self.dev_index + 1) % self.num_devices 

    def prev_device(self):
        self.dev_index = (self.dev_index - 1) % self.num_devices
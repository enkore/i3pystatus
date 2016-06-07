from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell


class DeviceNotFound(Exception):
    pass


class NoBatteryStatus(Exception):
    message = None

    def __init__(self, message):
        self.message = message


class Solaar(IntervalModule):
    """
    Shows status and load percentage of bluetooth-device

    .. rubric:: Available formatters

    * `{output}` — percentage of battery and status
    """

    color = "#FFFFFF"
    error_color = "#FF0000"
    interval = 30

    settings = (
        ("nameOfDevice", "name of the bluetooth-device"),
        ("color", "standard color"),
        ("error_color", "color to use when non zero exit code is returned"),
    )

    required = ("nameOfDevice",)

    def findDeviceNumber(self):
        command = 'solaar-cli show'
        retvalue, out, stderr = run_through_shell(command, enable_shell=True)
        for line in out.split('\n'):
            if line.count(self.nameOfDevice) > 0 and line.count(':') > 0:
                numberOfDevice = line.split(':')[0]
                return numberOfDevice
        raise DeviceNotFound()

    def findBatteryStatus(self, numberOfDevice):
        command = 'solaar-cli show -v %s' % (numberOfDevice)
        retvalue, out, stderr = run_through_shell(command, enable_shell=True)
        for line in out.split('\n'):
            if line.count('Battery') > 0:
                if line.count(':') > 0:
                    batterystatus = line.split(':')[1].strip().strip(",")
                    return batterystatus
                elif line.count('offline'):
                    raise NoBatteryStatus('offline')
                else:
                    raise NoBatteryStatus('unknown')
        raise NoBatteryStatus('unknown/error')

    def run(self):
        self.output = {}

        try:
            device_number = self.findDeviceNumber()
            output = self.findBatteryStatus(device_number)
            self.output['color'] = self.color
        except DeviceNotFound:
            output = "device absent"
            self.output['color'] = self.error_color
        except NoBatteryStatus as e:
            output = e.message
            self.output['color'] = self.error_color

        self.output['full_text'] = output

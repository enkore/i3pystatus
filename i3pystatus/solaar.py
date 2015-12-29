from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell


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
                return(0, numberOfDevice)
        return(1, 0)

    def findBatteryStatus(self, numberOfDevice):
        command = 'solaar-cli show -v %s' % (numberOfDevice)
        retvalue, out, stderr = run_through_shell(command, enable_shell=True)
        for line in out.split('\n'):
            if line.count('Battery') > 0:
                if line.count(':') > 0:
                    batterystatus = line.split(':')[1].strip().strip(",")
                    return(0, batterystatus)
                else:
                    return(1, 0)
        return(1, 0)

    def run(self):
        self.output = {}
        rcfindDeviceNumber = self.findDeviceNumber()
        if rcfindDeviceNumber[0] != 0:
            output = "problem finding device %s" % (self.nameOfDevice)
            self.output['color'] = self.error_color
        else:
            numberOfDevice = rcfindDeviceNumber[1]
            rcfindBatteryStatus = self.findBatteryStatus(numberOfDevice)
            if rcfindBatteryStatus[0] != 0:
                output = "problem finding battery status device %s" % (self.nameOfDevice)
                self.output['color'] = self.error_color
            else:
                output = self.findBatteryStatus(self.findDeviceNumber()[1])[1]
                self.output['color'] = self.color
        self.output['full_text'] = output

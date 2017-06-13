from i3pystatus import SettingsBase
from i3pystatus.core.command import run_through_shell
import re
import os

__author__ = 'drwahl'


class File(SettingsBase):
    """
    Monitor OpenVPN client.

    .. note::
        This OpenVPN backend relies on the "writepid" option during OpenVPN startup.
        If this option is not passed during startup, this backend will not be able
        to determine the status of the client.
    """

    conf_file = '/etc/openvpn/openvpn.conf'
    pid_file = ''
    openvpn_pid = False
    up_command = 'sudo openvpn --config %s' % conf_file

    settings = (
        ("conf_file", "Config file for this openvpn connection."),
        ("pid_file", "If not supplying a config file, just the PID file will suffice."),
        ("up_command", "Command to bring the openvpn connection up."),
    )


    def init(self):
        if not self.conf_file and not self.pid_file:
            raise Exception("either conf_file or pid_file must be passed in")


    def toggle_connection(self):
        if self.conf_file:
            if self.connected:
                os.kill(self.openvpn_pid, signal.SIGKILL)
            else:
                run_through_shell(self.up_command, enable_shell=True)


    def find_pid(self):
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        if self.openvpn_pid in pids:
            return True
        else:
            return False


    @property
    def connected(self):

        # get pid_file from config
        if self.conf_file:
            p = re.compile('^writepid .*')
            f = open(self.conf_file)
            for line in f.readlines():
                if p.match(line):
                    pid_file = line.split()[1]
            f.close()
        else:
            pid_file = self.pid_file

        # read pid from pid_file
        f = open(pid_file)
        self.openvpn_pid = f.readlines()[0].split()[0]
        f.close()

        return self.find_pid()

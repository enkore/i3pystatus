from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell

__author__ = 'facetoe'


class OpenVPN(IntervalModule):
    """
    Monitor OpenVPN connections.

    .. note::
        This module currently only supports systemd. Additionally, as of
        OpenVPN 2.4 the unit names have changed, as the OpenVPN server and
        client now have distinct unit files (``openvpn-server@.service`` and
        ``openvpn-client@.service``, respectively). Those who have updated to
        OpenVPN 2.4 will need to manually set the ``status_command``,
        ``vpn_up_command``, and ``vpn_down_command``.

    Formatters:

    * {vpn_name} — Same as setting.
    * {status} — Unicode up or down symbol.
    * {output} — Output of status_command.
    * {label} — Label for this connection, if defined.

    """

    color_up = "#00ff00"
    color_down = "#FF0000"
    status_up = '▲'
    status_down = '▼'
    format = "{vpn_name} {status}"
    status_command = "bash -c 'systemctl show openvpn@%(vpn_name)s | grep ActiveState=active'"

    vpn_up_command = "sudo /bin/systemctl start openvpn@%(vpn_name)s.service"
    vpn_down_command = "sudo /bin/systemctl stop openvpn@%(vpn_name)s.service"

    connected = False
    label = ''
    vpn_name = ''

    settings = (
        ("format", "Format string"),
        ("color_up", "VPN is up"),
        ("color_down", "VPN is down"),
        ("status_down", "Symbol to display when down"),
        ("status_up", "Symbol to display when up"),
        ("vpn_name", "Name of VPN"),
        ("vpn_up_command", "Command to bring up the VPN - default requires editing /etc/sudoers"),
        ("vpn_down_command", "Command to bring up the VPN - default requires editing /etc/sudoers"),
        ("status_command", "command to find out if the VPN is active"),
    )

    def init(self):
        if not self.vpn_name:
            raise Exception("vpn_name is required")
        
        # use new service names if openvpn version is 2.4 (2.5 is not out yet...)
        if run_through_shell('openvpn --version | grep -i "openvpn 2.4"', True).out.strip():
            status_command = "bash -c 'systemctl show openvpn-client@%(vpn_name)s | grep ActiveState=active'"
            vpn_up_command = "sudo /bin/systemctl start openvpn-client@%(vpn_name)s.service"
            vpn_down_command = "sudo /bin/systemctl stop openvpn-client@%(vpn_name)s.service"
       
    def toggle_connection(self):
        if self.connected:
            command = self.vpn_down_command
        else:
            command = self.vpn_up_command
        run_through_shell(command % {'vpn_name': self.vpn_name}, enable_shell=True)

    def on_click(self, button, **kwargs):
        self.toggle_connection()

    def run(self):
        command_result = run_through_shell(self.status_command % {'vpn_name': self.vpn_name}, enable_shell=True)
        self.connected = True if command_result.out.strip() else False

        if self.connected:
            color, status = self.color_up, self.status_up
        else:
            color, status = self.color_down, self.status_down

        vpn_name = self.vpn_name
        label = self.label

        self.data = locals()
        self.output = {
            "full_text": self.format.format(**locals()),
            'color': color,
        }

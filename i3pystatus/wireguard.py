from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell

__author__ = 'Pluggi'


class Wireguard(IntervalModule):
    """
    Monitor Wireguard connections.

    .. note::
        You might want to add something like this to /etc/sudoers:

        ``%wheel ALL = NOPASSWD: /bin/systemctl start wg-quick@wg0.service,/bin/systemctl stop wg-quick@wg0.service``

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

    status_command = "systemctl is-active wg-quick@{vpn_name}"
    vpn_up_command = "sudo /bin/systemctl start wg-quick@{vpn_name}.service"
    vpn_down_command = "sudo /bin/systemctl stop wg-quick@{vpn_name}.service"

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

    def toggle_connection(self):
        if self.connected:
            command = self.vpn_down_command
        else:
            command = self.vpn_up_command
        run_through_shell(command.format(vpn_name=self.vpn_name))

    def on_click(self, button, **kwargs):
        self.toggle_connection()

    def run(self):
        command_result = run_through_shell(self.status_command.format(vpn_name=self.vpn_name))
        self.connected = command_result.rc == 0

        if self.connected:
            color, status = self.color_up, self.status_up
        else:
            color, status = self.color_down, self.status_down

        vpn_name = self.vpn_name
        label = self.label

        self.data = locals()
        self.output = {
            "full_text": self.format.format(**self.data),
            'color': color,
        }

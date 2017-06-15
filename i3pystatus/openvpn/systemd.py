from i3pystatus import SettingsBase
from i3pystatus.core.command import run_through_shell

__author__ = 'facetoe'


class Systemd(SettingsBase):
    """
    Monitor systemd managed OpenVPN connections.

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

    use_new_service_name = False
    status_command = "bash -c 'systemctl show openvpn@%(vpn_name)s | grep ActiveState=active'"
    vpn_up_command = "sudo /bin/systemctl start openvpn@%(vpn_name)s.service"
    vpn_down_command = "sudo /bin/systemctl stop openvpn@%(vpn_name)s.service"
    name = False

    settings = (
        ("use_new_service_name", "Use new openvpn service names (openvpn 2.4^)"),
        ("vpn_up_command", "Command to bring up the VPN - default requires editing /etc/sudoers"),
        ("vpn_down_command", "Command to bring up the VPN - default requires editing /etc/sudoers"),
        ("status_command", "command to find out if the VPN is active"),
        ("name", "Systemd name of this VPN connection."),
    )

    def init(self):
        if not self.name:
            raise Exception("name is required")

        if self.use_new_service_name:
            self.status_command = "bash -c 'systemctl show openvpn-client@%(name)s | grep ActiveState=active'"
            self.vpn_up_command = "sudo /bin/systemctl start openvpn-client@%(name)s.service"
            self.vpn_down_command = "sudo /bin/systemctl stop openvpn-client@%(name)s.service"

    def toggle_connection(self):
        if self.connected:
            command = self.vpn_down_command
        else:
            command = self.vpn_up_command
        run_through_shell(command % {'name': self.name}, enable_shell=True)

    @property
    def connected(self):
        command_result = run_through_shell(self.status_command % {'name': self.name}, enable_shell=True)
        connected = True if command_result.out.strip() else False

        return connected

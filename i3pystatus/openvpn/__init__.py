from i3pystatus import IntervalModule


class Openvpn(IntervalModule):
    """
    Generic OpenVPN manager

    The `backends` setting determines the backends to use. For available backends see :ref:`openvpnbackends`.
    """

    settings = (
        ("backend", "OpenVPN management backend (instances of ``i3pystatus.openvpn.xxx.zzz``, e.g. :py:class:`.file.File`)"),
        ("format", "Format string"),
        ("color_up", "VPN is up"),
        ("color_down", "VPN is down"),
        ("vpn_name", "Name of this VPN connection"),
        ("label", "Label for this VPN connection"),
        ("status_down", "Symbol to display when down"),
        ("status_up", "Symbol to display when up"),
    )

    color_up = "#00ff00"
    color_down = "#FF0000"
    status_up = '▲'
    status_down = '▼'
    vpn_name = 'OpenVPN'
    label = ''
    format = "{vpn_name} {status}"
    backend = None
    connected = False
    on_leftclick = ['toggle_connection']

    def toggle_connection(self):
        self.backend.toggle_connection()

    def run(self):
        self.backend.init()

        self.connected = self.backend.connected

        if self.connected:
            color, status = self.color_up, self.status_up
        else:
            color, status = self.color_down, self.status_down

        vpn_name = self.vpn_name
        label = self.label

        self.data = locals()
        self.output = {
            "full_text": self.format.format(**locals()),
            "color": color
        }

from i3pystatus import IntervalModule
# requires python-novaclient
from novaclient.v2 import client
import webbrowser


class Openstack_vms(IntervalModule):
    """
    Displays the number of VMs in an openstack cluster in ACTIVE and
    non-ACTIVE states.
    Requires: python-novaclient
    """

    settings = (
        ("auth_url", "OpenStack cluster authentication URL (OS_AUTH_URL)"),
        ("username", "Username for OpenStack authentication (OS_USERNAME)"),
        ("password", "Password for Openstack authentication (OS_PASSWORD)"),
        ("tenant_name", "Tenant/Project name to view (OS_TENANT_NAME)"),
        ("color", "Display color when non-active VMs are =< `threshold`"),
        ("crit_color", "Display color when non-active VMs are => `threshold`"),
        ("threshold", "Set critical indicators when non-active VM pass this "
            "number"),
        ("horizon_url", "When clicked, open this URL in a browser"),
        "format"
    )
    required = ("auth_url", "password", "tenant_name", "username")
    color = "#00FF00"
    crit_color = "#FF0000"
    threshold = 0
    horizon_url = None
    format = "{tenant_name}: {active_servers} up, "\
        "{nonactive_servers} down"

    on_leftclick = "openurl"

    def run(self):
        nclient = client.Client(
            self.username,
            self.password,
            self.tenant_name,
            self.auth_url
        )

        active_servers = 0
        nonactive_servers = 0
        server_list = nclient.servers.list()
        for server in server_list:
            if server.status == 'ACTIVE':
                active_servers = active_servers + 1
            else:
                nonactive_servers = nonactive_servers + 1

        if nonactive_servers > self.threshold:
            display_color = self.crit_color
        else:
            display_color = self.color
        cdict = {
            "tenant_name": self.tenant_name,
            "active_servers": active_servers,
            "nonactive_servers": nonactive_servers,
        }

        self.data = cdict
        self.output = {
            "full_text": self.format.format(**cdict),
            "color": display_color
        }

    def openurl(self):
        webbrowser.open_new_tab(self.horizon_url)

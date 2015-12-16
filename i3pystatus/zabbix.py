from i3pystatus import IntervalModule
from pyzabbix import ZabbixAPI


class Zabbix(IntervalModule):
    """
    Zabbix alerts watcher

    Requires pyzabbix
    """
    settings = (
        ("zabbix_server", "Zabbix Server URL"),
        ("zabbix_user", "Zabbix API User"),
        ("zabbix_password", "Zabbix users password"),
        ("interval", "Update interval"),
        "format"
    )
    required = ("zabbix_server", "zabbix_user", "zabbix_password")
    interval = 60
    format = "{default}"

    def run(self):

        alerts_color = ["#DBDBDB", "#D6F6FF", "#FFF6A5", "#FFB689", "#FF9999", "#FF3838"]
        zapi = ZabbixAPI(self.zabbix_server)
        zapi.login(self.zabbix_user, self.zabbix_password)
        triggers = zapi.trigger.get(only_true=1,
                                    skipDependent=1,
                                    monitored=1,
                                    active=1,
                                    min_severity=2,
                                    output=["priority"],
                                    withLastEventUnacknowledged=1,
                                    )
        alerts_list = [t['priority'] for t in triggers]
        alerts = [0, 0, 0, 0, 0, 0]
        colors = []
        for i in range(0, 6):
                alerts[i] = alerts_list.count(str(i))
                if alerts[i] == 0:
                    alerts_color[i] = "#FFFFFF"


        cdict = {
            "default": "{0}:{a[5]}/{a[4]}/{a[3]}/{a[2]}/{a[1]}/{a[0]}".format(sum(alerts), a=alerts),
            "a5": alerts[5],
            "a4": alerts[4],
            "a3": alerts[3],
            "a2": alerts[2],
            "a1": alerts[1],
            "a0": alerts[0],
            "c5": alerts_color[5],
            "c4": alerts_color[4],
            "c3": alerts_color[3],
            "c2": alerts_color[2],
            "c1": alerts_color[1],
            "c0": alerts_color[0],
            "total": sum(alerts)
        }

        self.output = {
            "full_text": self.format.format(**cdict)
        }

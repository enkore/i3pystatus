from i3pystatus import IntervalModule
from pyzabbix import ZabbixAPI


class Zabbix(IntervalModule):
    """
    Zabbix alerts watcher

    Requires: pyzabbix

    .. rubric:: Available formatters

    * {default} - Full output count alerts like total:a5/a4/a3/a2/a1/a0
    * {total} - Total count of alerts
    * {aX_count} - Count alerts of X severity
    * {colorX} - Predicted color for X severity. It can be used with Pango markup hint for different colours at each severity with
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
        try:
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
            cdict = {}
            for i in range(0, 6):
                alerts[i] = alerts_list.count(str(i))
                cdict["a%s_count" % i] = alerts[i]
                if alerts[i] == 0:
                    cdict["color%s" % i] = "#FFFFFF"
                else:
                    cdict["color%s" % i] = alerts_color[i]

            cdict["default"] = "{0}:{a[5]}/{a[4]}/{a[3]}/{a[2]}/{a[1]}/{a[0]}".format(sum(alerts), a=alerts)
            cdict["total"] = sum(alerts)
            if alerts_list:
                color = alerts_color[max(map(int, alerts_list))]
            else:
                color = alerts_color[0]
            result = self.format.format(**cdict)

        except Exception as e:
            result = "Zabbix connection error"
            color = "#FF0000"

        self.output = {
            "full_text": result,
            "color": color
        }

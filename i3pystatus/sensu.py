from i3pystatus import IntervalModule, formatp

from enum import IntEnum
import requests
from urllib.parse import urljoin


class SensuCheck(IntervalModule):
    """ Pool sensu api events

    .. rubric:: Available formatters

    * {status} OK if not events else numbers of events
    * {last_event} Display the output of the most recent event (with priority on error event)
    """
    interval = 5

    required = ("api_url",)

    settings = (

        ("api_url", "URL of Sensu API. e.g: http://localhost/sensu/"),
        "api_username",
        "api_password",
        "format",
        "color_error",
        "color_warn",
        "color_ok",
        ("last_event_label", "Label to put before the last event output (default 'Last:')"),
        ("max_event_field", "Defines max length of the last_event message field "
                            "(default: 50)"),
    )

    api_url = None
    api_username = None
    api_password = None

    format = "{status}"
    color_error = "#ff0000"
    color_warn = "#f9ba46"
    color_ok = "#00ff00"
    last_event_label = "Last:"
    max_event_field = 50

    def run(self):
        try:
            auth = ()
            if self.api_username:
                auth = (self.api_username, self.api_password or "")

            response = requests.get(urljoin(self.api_url, "events"), auth=auth)
            if response.status_code != requests.codes.OK:
                self.error("could not query sensu api: {}".format(response.status_code))
            else:
                try:
                    events = response.json()
                except ValueError:
                    self.error("could not decode json")
                else:
                    try:
                        self.set_output(events)
                    except KeyError as exc:
                        self.error("could not find field {!s} in event".format(exc))
        except Exception as exc:
            self.output = {
                "full_text": "FAILED: {!s}".format(str(exc)),
                "color": self.color_error,
            }

    def set_output(self, events):
        events = sorted(
            [e for e in events if e["action"] != "resolve" and not e["silenced"]],
            key=lambda x: x["last_ok"],
            reverse=True
        )

        last_event_output = ""
        if not events:
            status = "OK"
            color = self.color_ok
        else:
            error = None
            try:
                error = next(e for e in events if e["check"]["status"] == SensuStatus.critical)
            except StopIteration:
                last_event = events[0]
            else:
                last_event = error

            status = "{} event(s)".format(len(events))
            color = self.color_error if error else self.color_warn
            last_event_output = self.get_event_output(last_event)

        self.output = {
            "full_text": formatp(self.format, status=status, last_event=last_event_output),
            "color": color,
        }

    def get_event_output(self, event):
        output = (event["check"]["output"] or "").replace("\n", " ")
        if self.last_event_label:
            output = "{} {}".format(self.last_event_label, output)

        if self.max_event_field and len(output) > self.max_event_field:
            output = output[:self.max_event_field]

        return output

    def error(self, error_msg):
        self.output = {
            "full_text": error_msg,
            "color": self.color_error,
        }


class SensuStatus(IntEnum):
    ok = 0
    warn = 1
    critical = 2
    unknown = 3

from datetime import datetime, timedelta
from urllib.request import urlopen
from subprocess import check_output
from json import loads

from i3pystatus import IntervalModule


class WifiOnIceAPI(IntervalModule):
    """
    Displays information about your current trip on Deutsche Bahn trains.

    Requires the PyPI package `basiciw` if you want to use automatic
    detection. See below on how to disable automatic detection based on
    wifi adapter names.

    .. rubric:: Available formatters

    For `format_delay` option:

    * `{delay}` - delay of train in minutes

    For `format_network_info` option:

    * `{currently}` - current state of network quality
    * `{duration}` - how long until the next network quality change
    * `{expected}` - next state of network quality

    For `format_next_stop` option:

    * `{station}` - Station name
    * `{platform}` - Platform number or name
    * `{arrival_time}` - Arrival time of train at the station (actual, if available, otherwise scheduled)
    * `{arrival_in}` - Time until arrival (in form "1h 12m" or "53m")
    * `{delay}` - Output of `format_delay` (or empty if no delay)`

    For `format_output` formatter:

    * `{speed}` - Train speed in km/h
    * `{next_stop}` - Output of `format_next_stop` (or `final_destination` option)
    * `{network_info}` - Output of `format_network_info` (or empty if neither current nor next info is known)
    """

    final_destination = 'Endstation, bitte aussteigen!'
    format_delay = ' | <span color="#FF0000">{delay_minutes}</span>'
    format_network_info = ' <span color="#999999">(Net: {currently} > [{duration}] {expected})</span>'
    format_next_stop = '{station} <span color="#999999">[{platform}]</span> {arrival_time} ({arrival_in}{delay})'
    format_output = '<span color="#999999">{speed}km/h</span> > {next_stop}{network_info}'
    ice_status = {}
    interval = 2
    on_leftclick = 'open_travelynx'
    travelynx_url = 'travelynx.de'
    trip_info = {}
    wifi_adapters = ['wlan0']
    wifi_names = ['wifi@db', 'wifionice']

    settings = (
        ("final_destination", "Information text for 'final destination has been reached'"),
        ("format_delay", "Formatter for delay information"),
        ("format_network_info", "Formatter for network information"),
        ("format_next_stop", "Formatter for next stop information"),
        ("format_output", "Formatter for output to i3bar"),
        ("travelynx_url", "URL of your travelynx page"),
        ("wifi_adapters", "List of wifi adapters the module should consider "
                          "when detecting if you are in a train. Set to `None` "
                          "to disable that functionality."),
        ("wifi_names", "List of Wifi network names that should be considered 'on a train'."),
    )

    def _format_time(self, seconds):
        if seconds is None:
            return "?"
        seconds = int(seconds)
        components = []
        if seconds >= 3600:
            hours = int(seconds / 3600)
            seconds -= hours * 3600
            components.append('{}h'.format(hours))
        if seconds >= 60:
            minutes = int(seconds / 60)
            seconds -= minutes * 60
            components.append('{}m'.format(minutes))
        if not components:
            components.append('now')
        return " ".join(components)

    def _get_data(self):
        trip_info_req = urlopen('https://iceportal.de/api1/rs/tripInfo/trip')
        self.trip_info = loads(trip_info_req.read())['trip']

        ice_status_req = urlopen('https://iceportal.de/api1/rs/status')
        self.ice_status = loads(ice_status_req.read())

    def _check_wifi(self):
        if self.wifi_adapters is None:
            return True

        from basiciw import iwinfo
        for adapter in self.wifi_adapters:
            iwi = iwinfo(adapter)
            for wifi in self.wifi_names:
                if iwi['essid'].lower() == wifi.lower():
                    return True
        return False

    def open_travelynx(self):
        if not self._check_wifi():
            return None
        if not self.trip_info:
            self._get_data()
        check_output(['xdg-open', 'https://{}/s/{}?train={}%20{}'.format(
            self.travelynx_url,
            self.trip_info['stopInfo']['actualLast'],
            self.trip_info['trainType'],
            self.trip_info['vzn'],
        )])

    def run(self):
        if self._check_wifi():
            self._get_data()
            now = datetime.now()

            next_stop_id = self.trip_info['stopInfo']['actualNext']
            for stop in self.trip_info['stops']:
                if stop['station']['evaNr'] == next_stop_id:
                    if stop['timetable']['departureDelay']:
                        delay = self.format_delay.format(
                            delay=stop['timetable']['departureDelay'],
                        )
                    else:
                        delay = ''

                    if stop['timetable'].get('actualArrivalTime', 0):
                        arrival = datetime.fromtimestamp(stop['timetable']['actualArrivalTime'] / 1000)
                        arrival_in = arrival - now
                    elif stop['timetable'].get('scheduledArrivalTime', 0):
                        arrival = datetime.fromtimestamp(stop['timetable']['scheduledArrivalTime'] / 1000)
                        arrival_in = arrival - now
                    else:
                        arrival = datetime.now()
                        arrival_in = timedelta()

                    next_stop = self.format_next_stop.format(
                        station=stop['station']['name'],
                        platform=stop['track']['actual'],
                        arrival_time=arrival.strftime('%H:%M'),
                        arrival_in=self._format_time(arrival_in.total_seconds()),
                        delay=delay
                    )
                    break
            else:
                next_stop = self.final_destination

            net_current = self.ice_status['connectivity']['currentState']
            net_future = self.ice_status['connectivity']['nextState']

            if net_current not in (None, 'NO_INFO') or net_future not in (None, 'NO_INFO'):
                net = self.format_network_info.format(
                    currently=net_current,
                    duration=self._format_time(self.ice_status['connectivity']['remainingTimeSeconds']),
                    expected=net_future,
                )
            else:
                net = ''

            self.output = {
                'full_text': self.format_output.format(
                    speed=self.ice_status['speed'],
                    next_stop=next_stop,
                    network_info=net,
                ),
                'markup': 'pango',
            }
        else:
            self.output = None

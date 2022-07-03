from datetime import datetime, timedelta
from json import loads
from urllib.request import urlopen
from threading import Condition, Thread

from i3pystatus import Module
from i3pystatus.core.util import formatp, user_open


class WifiOnIceAPI(Module):
    """
    Displays information about your current trip on Deutsche Bahn trains.
    The default behaviour on left-click is to send you to travelynx for
    easy check-in to the train.

    Requires the PyPI package `basiciw` if you want to use automatic
    detection. See below on how to disable automatic detection based on
    wifi adapter names.

    .. rubric:: Available formatters

    * `{arrival_in}` - Time until arrival (in form "1h 12m" or "53m")
    * `{arrival_time}` - Arrival time of train at the station (actual, if available, otherwise scheduled)
    * `{delay}` - delay of train in minutes
    * `{net_current}` - current state of network quality
    * `{net_duration}` - how long until the next network quality change
    * `{net_expected}` - next state of network quality
    * `{next_platform}` - Platform number or name
    * `{next_station}` - Station name
    * `{speed}` - Train speed in km/h
    """

    final_destination = 'Endstation'
    format_offtrain = None
    format_ontrain = '{speed}km/h > {next_station} ({arrival_in}[ | {delay_minutes}])'
    ice_status = {}
    off_train_interval = 10
    on_leftclick = 'open_travelynx'
    on_train_interval = 2
    travelynx_url = 'travelynx.de'
    trip_info = {}
    wifi_adapters = ['wlan0']
    wifi_names = ['WiFi@DB', 'WIFIonICE']

    settings = (
        ("final_destination", "Information text for 'final destination has been reached'"),
        ("format_ontrain", "Formatter for 'on a train'"),
        ("format_offtrain", "Formatter for 'not on a train' (module hidden if `None` - no formatters available)"),
        ("off_train_interval", "time between updates if no train is detected"),
        ("on_train_interval", "time between updates while on a train"),
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

    def _loop(self):
        while True:

            if self._check_wifi():
                try:
                    trip_info_req = urlopen('https://iceportal.de/api1/rs/tripInfo/trip')
                    self.trip_info = loads(trip_info_req.read())['trip']

                    ice_status_req = urlopen('https://iceportal.de/api1/rs/status')
                    self.ice_status = loads(ice_status_req.read())
                except Exception:
                    self.trip_info = {}
                    self.ice_status = {}

                self.update_bar()

                with self.condition:
                    self.condition.wait(self.on_train_interval)
            else:
                self.trip_info = {}
                self.ice_status = {}

                self.update_bar()

                with self.condition:
                    self.condition.wait(self.off_train_interval)

    def init(self):
        self.condition = Condition()
        self.thread = Thread(
            target=self._loop,
            daemon=True
        )
        self.thread.start()

    def open_travelynx(self):
        if not self.trip_info:
            return

        user_open('https://{}/s/{}?train={}%20{}'.format(
            self.travelynx_url,
            self.trip_info['stopInfo']['actualLast'],
            self.trip_info['trainType'],
            self.trip_info['vzn'],
        ))

    def update_bar(self):
        if self.trip_info and self.ice_status:
            format_vars = {
                'arrival_in': '?',
                'arrival_time': '',
                'net_current': '',
                'net_duration': '?',
                'net_expected': '',
                'next_platform': '',
                'next_station': self.final_destination,
                'speed': self.ice_status['speed'],
            }

            next_stop_id = self.trip_info['stopInfo']['actualNext']
            now = datetime.now()
            for stop in self.trip_info['stops']:
                if stop['station']['evaNr'] == next_stop_id:
                    if stop['timetable']['departureDelay']:
                        format_vars['delay'] = stop['timetable']['departureDelay'],
                    else:
                        format_vars['delay'] = 0

                    if stop['timetable'].get('actualArrivalTime', 0):
                        arrival = datetime.fromtimestamp(stop['timetable']['actualArrivalTime'] / 1000)
                        arrival_in = arrival - now
                    elif stop['timetable'].get('scheduledArrivalTime', 0):
                        arrival = datetime.fromtimestamp(stop['timetable']['scheduledArrivalTime'] / 1000)
                        arrival_in = arrival - now
                    else:
                        arrival = datetime.now()
                        arrival_in = timedelta()

                    format_vars['next_station'] = stop['station']['name']
                    format_vars['next_platform'] = stop['track']['actual']
                    format_vars['arrival_time'] = arrival.strftime('%H:%M')
                    format_vars['arrival_in'] = self._format_time(arrival_in.total_seconds())
                    break

            net_current = self.ice_status['connectivity']['currentState']
            net_future = self.ice_status['connectivity']['nextState']

            if net_current not in (None, 'NO_INFO') or net_future not in (None, 'NO_INFO'):
                format_vars['net_current'] = net_current
                format_vars['net_expected'] = net_expected
                format_vars['net_duration'] = self._format_time(self.ice_status['connectivity']['remainingTimeSeconds'])

            self.output = {
                'full_text': formatp(self.format_ontrain, **format_vars).strip(),
            }
        else:
            if self.format_offtrain is not None:
                self.output = {
                    'full_text': self.format_offtrain,
                }
            else:
                self.output = None

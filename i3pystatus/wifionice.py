from datetime import datetime, timedelta
from json import loads
from urllib.request import urlopen
from threading import Condition, Thread

from i3pystatus import Module
from i3pystatus.core.util import formatp, user_open


class WifiOnIceAPI(Module):
    """
    Displays information about your current trip on Deutsche Bahn trains.
    Allows you to open an url formatted using train information.

    Requires the PyPI package `basiciw` if you want to use automatic
    detection. See below on how to disable automatic detection based on
    wifi adapter names.

    .. rubric:: URL examples

    * `https://travelynx.de/s/{last_station_no}?train={train_type}%20{train_no}` - Open travelynx check in page
    * `https://bahn.expert/details/{train_type}%20{train_no}/{trip_date}/?station={next_station_no}` - Show bahn.expert view for next station

    .. rubric:: Available formatters

    * `{arrival_in}` - Time until arrival (in form "1h 12m" or "53m")
    * `{arrival_time}` - Arrival time of train at the station (actual, if available, otherwise scheduled)
    * `{delay}` - delay of train in minutes
    * `{gps_lat}` - Current GPS latitude
    * `{gps_lon}` - Current GPS longitude
    * `{last_station_no}` - EVA number of the previous stop
    * `{net_current}` - current state of network quality
    * `{net_duration}` - how long until the next network quality change
    * `{net_expected}` - next state of network quality
    * `{next_platform}` - Platform number or name
    * `{next_station_no}` - EVA number of the next stop
    * `{next_station}` - Station name
    * `{speed}` - Train speed in km/h
    * `{train_no}` - Train number
    * `{train_type}` - Train Type (probably always `ICE`)
    """

    final_destination = 'Endstation'
    format_offtrain = None
    format_ontrain = '{speed}km/h > {next_station} ({arrival_in}[ | {delay}])'
    ice_status = {}
    off_train_interval = 10
    on_leftclick = 'open_url'
    on_train_interval = 2
    trip_info = {}
    url_on_click = ''
    wifi_adapters = ['wlan0']
    wifi_names = ['WiFi@DB', 'WIFIonICE']

    settings = (
        ("final_destination", "Information text for 'final destination has been reached'"),
        ("format_offtrain", "Formatter for 'not on a train' (module hidden if `None` - no formatters available)"),
        ("format_ontrain", "Formatter for 'on a train'"),
        ("off_train_interval", "time between updates if no train is detected"),
        ("on_train_interval", "time between updates while on a train"),
        ("url_on_click", "URL to open when left-clicking the module"),
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
            components.append(f'{hours}h')
        if seconds >= 60:
            minutes = int(seconds / 60)
            seconds -= minutes * 60
            components.append(f'{minutes}m')
        if not components:
            components.append('now')
        return " ".join(components)

    def _check_wifi(self):
        if self.wifi_adapters is None:
            self.logger.debug('Disabling automatic on-train detection because wifi_adapters is None')
            return True
        try:
            from basiciw import iwinfo
        except ModuleNotFoundError:
            self.logger.warning('Disabling automatic on-train detection because basiciw is not installed')
            return True
        for adapter in self.wifi_adapters:
            self.logger.info(f'Checking {adapter} for compatible wifi network')
            iwi = iwinfo(adapter)
            for wifi in self.wifi_names:
                if iwi['essid'].lower() == wifi.lower():
                    self.logger.info(f'{adapter} uses {wifi} - success!')
                    return True
        self.logger.info('No matching wifi connection found')
        return False

    def _loop(self):
        self.logger.debug('begin of _loop()')
        while True:
            self.logger.debug('new _loop()')
            if self._check_wifi():
                self.logger.info('On a train :)')
                try:
                    trip_info_req = urlopen('https://iceportal.de/api1/rs/tripInfo/trip')
                    self.trip_info = loads(trip_info_req.read())['trip']

                    ice_status_req = urlopen('https://iceportal.de/api1/rs/status')
                    self.ice_status = loads(ice_status_req.read())
                except Exception:
                    self.trip_info = {}
                    self.ice_status = {}

                self.logger.debug(f'trip_info: {self.trip_info!r}')
                self.logger.debug(f'ice_status: {self.ice_status!r}')

                self.update_bar()

                with self.condition:
                    self.condition.wait(self.on_train_interval)
            else:
                self.logger.info('Not on a train :(')

                self.trip_info = {}
                self.ice_status = {}

                self.logger.debug(f'trip_info: {self.trip_info!r}')
                self.logger.debug(f'ice_status: {self.ice_status!r}')

                self.update_bar()

                with self.condition:
                    self.condition.wait(self.off_train_interval)

    @property
    def _format_vars(self):
        format_vars = {
            'arrival_in': '?',
            'arrival_time': '',
            'gps_lat': self.ice_status['latitude'],
            'gps_lon': self.ice_status['longitude'],
            'last_station_no': self.trip_info['stopInfo']['actualLast'],
            'net_current': '',
            'net_duration': '?',
            'net_expected': '',
            'next_platform': '',
            'next_station': self.final_destination,
            'next_station_no': self.trip_info['stopInfo']['actualNext'],
            'speed': self.ice_status['speed'],
            'train_no': self.trip_info['vzn'],
            'train_type': self.trip_info['trainType'],
            'trip_date': self.trip_info['tripDate'],
        }

        next_stop_id = self.trip_info['stopInfo']['actualNext']
        now = datetime.now()
        for stop in self.trip_info['stops']:
            if stop['station']['evaNr'] == next_stop_id:
                if stop['timetable']['departureDelay']:
                    format_vars['delay'] = stop['timetable']['departureDelay']
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
            format_vars['net_expected'] = net_future
            format_vars['net_duration'] = self._format_time(self.ice_status['connectivity']['remainingTimeSeconds'])

        self.logger.debug(f'format_vars: {format_vars!r}')
        return format_vars

    def init(self):
        self.condition = Condition()
        self.thread = Thread(
            target=self._loop,
            daemon=True
        )
        self.thread.start()

    def open_url(self):
        if not (self.trip_info and self.ice_status and self.url_on_click):
            return

        user_open(self.url_on_click.format(**self._format_vars))

    def update_bar(self):
        if self.trip_info and self.ice_status:
            self.output = {
                'full_text': formatp(self.format_ontrain, **self._format_vars).strip(),
            }
        else:
            if self.format_offtrain is not None:
                self.output = {
                    'full_text': self.format_offtrain,
                }
            else:
                self.output = None

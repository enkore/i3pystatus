import logging
import shutil
import threading
import os
import xml.etree.ElementTree as etree
from datetime import datetime

import requests
import vlc
from dateutil import parser
from dateutil.tz import tzutc
from i3pystatus import IntervalModule
from i3pystatus.core.desktop import DesktopNotification
from i3pystatus.core.util import internet, require


class State:
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


class ABCRadio(IntervalModule):
    """
    Streams ABC Australia radio - https://radio.abc.net.au/. Currently uses VLC to do the
    actual streaming.

    Requires the PyPI packages `python-vlc`, `python-dateutil` and `requests`. Also requires VLC
    - https://www.videolan.org/vlc/index.html

    .. rubric:: Available formatters

    * `{station}` — Current station
    * `{title}` — Title of current show
    * `{url}` — Show's URL
    * `{remaining}` — Time left for current show
    * `{player_state}` — Unicode icons representing play, pause and stop
    """

    settings = (
        ("format", "format string for when the player is inactive"),
        ("format_playing", "format string for when the player is playing"),
        ("target_stations", "list of station ids to select from. Station ids can be obtained "
                            "from the following XML - http://www.abc.net.au/radio/data/stations_apps_v3.xml. "
                            "If the list is empty, all stations will be accessible."),
    )

    format = "{station} {title} {player_state}"
    format_playing = "{station} {title} {remaining} {player_state}"

    on_leftclick = 'toggle_play'
    on_upscroll = ['cycle_stations', 1]
    on_downscroll = ['cycle_stations', -1]
    on_doubleleftclick = 'display_notification'
    interval = 1

    # Destroy the player after this many seconds of inactivity
    PLAYER_LIFETIME = 5

    show_info = {}
    player = None
    station_info = None
    station_id = None
    stations = None
    prev_title = None
    prev_station = None
    target_stations = []

    end = None
    start = None
    destroy_timer = None
    cycle_lock = threading.Lock()

    player_icons = {
        State.PAUSED: "▷",
        State.PLAYING: "▶",
        State.STOPPED: "◾",
    }

    def init(self):
        self.station_info = ABCStationInfo()

    @require(internet)
    def run(self):
        if self.station_id is None:
            self.stations = self.station_info.get_stations()
            # Select the first station in the list
            self.cycle_stations(1)

        if self.end and self.end <= datetime.now(tz=tzutc()):
            self.update_show_info()

        format_dict = self.show_info.copy()
        format_dict['player_state'] = self.get_player_state()
        format_dict['remaining'] = self.get_remaining()

        format_template = self.format_playing if self.player else self.format
        self.output = {
            "full_text": format_template.format(**format_dict)
        }

    def update_show_info(self):
        log.debug("Updating: show_info - %s" % datetime.now())
        self.show_info = dict.fromkeys(
            ('title', 'url', 'start', 'end', 'duration', 'stream', 'remaining', 'station', 'description', 'title',
             'short_synopsis', 'url'), '')

        self.show_info.update(self.stations[self.station_id])
        self.show_info.update(self.station_info.currently_playing(self.station_id))

        # Show a notification when the show changes if the user is actively listening.
        should_show = self.prev_station == self.show_info['station'] and self.prev_title != self.show_info[
            'title'] and self.player
        if should_show:
            self.display_notification()
        self.prev_title = self.show_info['title']
        self.prev_station = self.show_info['station']

        self.end = self.show_info['end'] if self.show_info['end'] else None
        self.start = self.show_info['start'] if self.show_info['start'] else None

    def get_player_state(self):
        if self.player:
            return self.player_icons[self.player.player_state]
        else:
            return self.player_icons[State.STOPPED]

    def get_remaining(self):
        if self.end and self.end > datetime.now(tz=tzutc()):
            return str(self.end - datetime.now(tz=tzutc())).split(".")[0]
        return ''

    def cycle_stations(self, increment=1):
        with self.cycle_lock:
            target_array = self.target_stations if len(self.target_stations) > 0 else list(self.stations.keys())
            if self.station_id in target_array:
                next_index = (target_array.index(self.station_id) + increment) % len(target_array)
                self.station_id = target_array[next_index]
            else:
                self.station_id = target_array[0]

            log.debug("Cycle to: {}".format(self.station_id))
            if self.player:
                current_state = self.player.player_state
                self.player.stop()
            else:
                current_state = State.STOPPED

            self.update_show_info()
            if self.player:
                self.player.load_stream(self.show_info['stream'])
                self.player.set_state(current_state)

    def display_notification(self):
        if self.show_info:
            station, title, synopsis = self.show_info['station'], self.show_info['title'], self.show_info[
                'short_synopsis']
            title = "{} - {}".format(station, title)

            def get_image():
                image_link = self.show_info.get('image_link', None)
                if image_link:
                    try:
                        image_path = "/tmp/{}.icon".format(station)
                        if not os.path.isfile(image_path):
                            response = requests.get(image_link, stream=True)
                            with open(image_path, 'wb') as out_file:
                                shutil.copyfileobj(response.raw, out_file)
                        return image_path
                    except:
                        pass

            DesktopNotification(title=title, body=synopsis, icon=get_image()).display()
            log.info("Displayed notification")

    def toggle_play(self):
        if not self.player:
            self.init_player()

        if self.player.is_playing():
            self.player.pause()
            self.destroy_timer = threading.Timer(self.PLAYER_LIFETIME, self.destroy)
            self.destroy_timer.start()
        else:
            if self.destroy_timer:
                self.destroy_timer.cancel()
                self.destroy_timer = None
            self.player.play()
        self.run()

    def init_player(self):
        if self.show_info:
            self.player = VLCPlayer()
            log.info("Created player: {}".format(id(self.player)))
            if not self.player.stream_loaded():
                log.info("Loading stream: {}".format(self.show_info['stream']))
                self.player.load_stream(self.show_info['stream'])
            if not self.player.is_alive():
                self.player.start()

    def destroy(self):
        log.debug("Destroying player: {}".format(id(self.player)))
        if self.player:
            self.player.destroy()
        self.player = None


class ABCStationInfo:
    PLAYING_URL = "https://program.abcradio.net.au/api/v1/programitems/{}/live.json?include=now"

    def currently_playing(self, station_id):
        station_info = self._get(self.PLAYING_URL.format(station_id)).json()
        try:
            return dict(
                title=station_info['now']['program']['title'],
                url=station_info['now']['primary_webpage']['url'],
                start=parser.parse(station_info['now']['live'][0]['start']),
                end=parser.parse(station_info['now']['live'][0]['end']),
                duration=station_info['now']['live'][0]['duration_seconds'],
                short_synopsis=station_info['now']['short_synopsis'],
                stream=sorted(station_info['now']['live'][0]['outlets'][0]['audio_streams'], key=lambda x: x['type'])[0]['url']
            )
        except (KeyError, IndexError):
            return {}

    def get_stations(self):
        stations = dict()
        station_xml = etree.fromstring(self._get('http://www.abc.net.au/radio/data/stations_apps_v3.xml').content)
        for element in station_xml:
            attrib = element.attrib
            if attrib["showInAndroidApp"] == 'true':
                stations[attrib['id']] = dict(
                    id=attrib['id'],
                    station=attrib['name'],
                    description=attrib.get('description', None),
                    link=attrib.get('linkUrl', None),
                    image_link=attrib.get('WEBimageUrl', None),
                    stream=attrib.get('hlsStreamUrl', None),
                )
        return stations

    def _get(self, url):
        result = requests.get(url=url)
        if result.status_code not in range(200, 300):
            result.raise_for_status()
        return result


log = logging.getLogger(__name__)


class VLCPlayer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.idle = threading.Event()
        self.die = threading.Event()
        self.instance = vlc.Instance()
        self.player_state = State.STOPPED
        self.player = self.instance.media_player_new()

    def run(self):
        states = {
            State.STOPPED: self.player.stop,
            State.PLAYING: self.player.play,
            State.PAUSED: self.player.pause,
        }
        while not self.die.is_set():
            self.idle.wait()
            states[self.player_state]()
            self.idle.clear()

    def load_stream(self, url):
        self.player.set_media(self.instance.media_new(url))

    def stream_loaded(self):
        return self.player.get_media() is not None

    def play(self):
        self.set_state(State.PLAYING)

    def pause(self):
        self.set_state(State.PAUSED)

    def stop(self):
        self.set_state(State.STOPPED)

    def destroy(self):
        self.die.set()
        self.idle.set()
        self.player.stop()
        self.player.release()

    def set_state(self, state):
        log.info("{} -> {}".format(self.player_state, state))
        self.player_state = state
        self.idle.set()

    def is_playing(self):
        return self.player.is_playing()

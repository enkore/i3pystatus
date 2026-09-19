# -*- coding: utf-8 -*-
"""
i3pystatus module: wttr

Shows current weather conditions from wttr.in in the i3bar.

Install:
    Save this file as `wttr.py` and drop it directly into the
    i3pystatus package's modules directory.

Usage in your i3pystatus config (~/.config/i3pystatus/config.py):

    from i3pystatus.wttr import Wttr 

    status.register("wttr",
        location="High Point, North Carolina",
        units="F",
        format="{icon} {temp}°{units} (H:{temp_max}° L:{temp_min}°)",
        interval=600,
    )

Requires: requests
"""

import requests
from datetime import datetime
from i3pystatus import IntervalModule


class Wttr(IntervalModule):
    """
    Displays current weather conditions from wttr.in.

    Available formatters for `format`:
        {icon}          - weather glyph/emoji corresponding to conditions
        {temp}          - current temperature
        {temp_max}      - today's forecast high
        {temp_min}      - today's forecast low
        {feels_like}    - "feels like" temperature
        {units}         - "F" or "C", matching the `units` setting
        {condition}     - short text description (e.g. "Partly cloudy")
        {humidity}      - relative humidity, percent
        {wind_speed}    - wind speed in mph
        {wind_dir}      - wind direction (16-point compass, e.g. "NW")
        {pressure}      - pressure in millibars
        {uv_index}      - UV index
        {area_name}     - resolved location name
        {region}        - resolved region/state

    Note on {icon}: the glyph automatically switches to a night variant
    (e.g. clear sun -> crescent moon) when the local time is between
    today's sunrise and sunset, based on the NIGHT_ICONS table. This
    assumes the machine running i3pystatus and `location` share a timezone.
    """

    settings = (
        ("location", "Location string to query, e.g. 'High Point, North Carolina'"),
        ("units", "'F' for Fahrenheit or 'C' for Celsius"),
        ("format", "format string, see module docstring for available fields"),
        ("format_error", "format string used when a request fails"),
        ("colorize", "if True, set self.output color based on temperature"),
        ("color", "static color to use when colorize is False"),
        ("error_color", "color to use when a request fails"),
        ("icons", "dict mapping wttr.in weather codes to icon strings, "
                  "merged over the built-in WEATHER_ICONS table"),
    )

    required = ("location",)

    # Defaults (overridable via settings=... in status.register)
    location = None
    units = "F"
    format = "{icon} {temp}°{units} (H:{temp_max}° L:{temp_min}°)"
    format_error = "wttr: unavailable"
    colorize = True
    color = "#FFFFFF"
    error_color = "#FF0000"
    icons = None

    # wttr.in / worldweatheronline condition codes -> icon glyph.
    # These are plain emoji so they render without a Nerd Font. Swap in
    # Nerd Font glyphs (e.g. "" ""  etc.) if your bar font supports them.
    WEATHER_ICONS = {
        "113": "☀️",   # Sunny / Clear
        "116": "⛅",   # Partly cloudy
        "119": "☁️",   # Cloudy
        "122": "☁️",   # Overcast
        "143": "🌫️",  # Mist
        "176": "🌦️",  # Patchy rain possible
        "179": "🌨️",  # Patchy snow possible
        "182": "🌨️",  # Patchy sleet possible
        "185": "🌨️",  # Patchy freezing drizzle possible
        "200": "⛈️",  # Thundery outbreaks possible
        "227": "🌨️",  # Blowing snow
        "230": "❄️",   # Blizzard
        "248": "🌫️",  # Fog
        "260": "🌫️",  # Freezing fog
        "263": "🌦️",  # Patchy light drizzle
        "266": "🌦️",  # Light drizzle
        "281": "🌧️",  # Freezing drizzle
        "284": "🌧️",  # Heavy freezing drizzle
        "293": "🌦️",  # Patchy light rain
        "296": "🌧️",  # Light rain
        "299": "🌧️",  # Moderate rain at times
        "302": "🌧️",  # Moderate rain
        "305": "🌧️",  # Heavy rain at times
        "308": "🌧️",  # Heavy rain
        "311": "🌧️",  # Light freezing rain
        "314": "🌨️",  # Moderate or heavy freezing rain
        "317": "🌨️",  # Light sleet
        "320": "🌨️",  # Moderate or heavy sleet
        "323": "🌨️",  # Patchy light snow
        "326": "🌨️",  # Light snow
        "329": "🌨️",  # Patchy moderate snow
        "332": "❄️",   # Moderate snow
        "335": "❄️",   # Patchy heavy snow
        "338": "❄️",   # Heavy snow
        "350": "🌨️",  # Ice pellets
        "353": "🌦️",  # Light rain shower
        "356": "🌧️",  # Moderate or heavy rain shower
        "359": "🌧️",  # Torrential rain shower
        "362": "🌨️",  # Light sleet showers
        "365": "🌨️",  # Moderate or heavy sleet showers
        "368": "🌨️",  # Light snow showers
        "371": "❄️",   # Moderate or heavy snow showers
        "374": "🌨️",  # Light showers of ice pellets
        "377": "🌨️",  # Moderate or heavy showers of ice pellets
        "386": "⛈️",  # Patchy light rain with thunder
        "389": "⛈️",  # Moderate or heavy rain with thunder
        "392": "⛈️",  # Patchy light snow with thunder
        "395": "⛈️",  # Moderate or heavy snow with thunder
    }
    DEFAULT_ICON = "🌡️"

    # Overrides applied on top of WEATHER_ICONS when it's nighttime at the
    # queried location. Only condition codes that look meaningfully
    # different after dark need an entry here (e.g. sunny -> clear night);
    # rain/snow/storm glyphs already look fine regardless of time of day.
    NIGHT_ICONS = {
        "113": "🌙",   # Clear (sunny -> clear night)
        "116": "🌙☁️",  # Partly cloudy -> partly cloudy night
        "119": "☁️",   # Cloudy (unchanged)
        "122": "☁️",   # Overcast (unchanged)
    }

    interval = 600  # seconds; wttr.in doesn't need to be polled every second

    on_leftclick = "run"  # manual refresh on click

    def init(self):
        self._session = requests.Session()

    def run(self):
        try:
            data = self._fetch()
            parsed = self._parse(data)
            text = self.format.format(**parsed)
            color = self._pick_color(parsed) if self.colorize else self.color
            self.output = {
                "full_text": text,
                "color": color,
            }
        except (requests.exceptions.RequestException, KeyError, IndexError, ValueError) as e:
            self.logger.exception("wttr module failed to fetch/parse weather")
            self.output = {
                "full_text": self.format_error,
                "color": self.error_color,
            }

    def _fetch(self) -> dict:
        location = self.location.replace(" ", "+")
        url = f"https://wttr.in/{location}"
        response = self._session.get(url, params={"format": "j1"}, timeout=10)
        response.raise_for_status()
        return response.json()

    def _parse(self, data: dict) -> dict:
        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        today = data["weather"][0]  # weather[0] is always today's forecast

        use_fahrenheit = self.units.upper() == "F"
        temp = current["temp_F"] if use_fahrenheit else current["temp_C"]
        feels_like = current["FeelsLikeF"] if use_fahrenheit else current["FeelsLikeC"]
        temp_max = today["maxtempF"] if use_fahrenheit else today["maxtempC"]
        temp_min = today["mintempF"] if use_fahrenheit else today["mintempC"]

        weather_code = current["weatherCode"]
        is_day = self._is_daytime(today["astronomy"][0])
        icon = self._resolve_icon(weather_code, is_day)

        return {
            "icon": icon,
            "temp": temp,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "feels_like": feels_like,
            "units": "F" if use_fahrenheit else "C",
            "condition": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"],
            "wind_speed": current["windspeedMiles"],
            "wind_dir": current["winddir16Point"],
            "pressure": current["pressure"],
            "uv_index": current["uvIndex"],
            "area_name": area["areaName"][0]["value"],
            "region": area["region"][0]["value"],
        }

    def _is_daytime(self, astronomy: dict) -> bool:
        """
        Determine whether it's currently daytime at the queried location,
        based on today's sunrise/sunset times from wttr.in (e.g. "06:32 AM").

        This compares against the machine's local clock, so it assumes the
        machine running i3pystatus is in the same timezone as `location`.
        If the times can't be parsed for any reason, default to daytime
        so we fall back to the more common icon set.
        """
        try:
            now = datetime.now().time()
            sunrise = datetime.strptime(astronomy["sunrise"], "%I:%M %p").time()
            sunset = datetime.strptime(astronomy["sunset"], "%I:%M %p").time()
            return sunrise <= now <= sunset
        except (KeyError, ValueError):
            return True

    def _resolve_icon(self, weather_code: str, is_day: bool = True) -> str:
        """Look up the icon for a wttr.in weather code, honoring user overrides."""
        table = self.WEATHER_ICONS
        if not is_day:
            table = {**table, **self.NIGHT_ICONS}
        if self.icons:
            table = {**table, **self.icons}
        return table.get(str(weather_code), self.DEFAULT_ICON)

    def _pick_color(self, parsed: dict) -> str:
        """Simple color ramp based on temperature (assumes Fahrenheit scale)."""
        temp_f = float(parsed["temp"]) if parsed["units"] == "F" else float(parsed["temp"]) * 9 / 5 + 32
        if temp_f >= 90:
            return "#FF4500"  # hot - orange red
        elif temp_f >= 70:
            return "#FFD700"  # warm - gold
        elif temp_f >= 50:
            return "#ADFF2F"  # mild - green-yellow
        elif temp_f >= 32:
            return "#87CEEB"  # cool - sky blue
        else:
            return "#00BFFF"  # cold - deep sky blue

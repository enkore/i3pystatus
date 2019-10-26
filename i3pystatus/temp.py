from i3pystatus import IntervalModule
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.core.util import make_vertical_bar


class Sensor:
    """
    Simple class representing a CPU temperature sensor.
    """

    def __init__(self, name, current, maximum, critical):
        self.name = name.replace(' ', '_')
        self.current = int(current)
        self.maximum = int(maximum) if maximum else int(critical)
        self.critical = int(critical)

    def __repr__(self):
        return "Sensor(name='{}', current={}, maximum={}, critical={})".format(
            self.name,
            self.current,
            self.maximum,
            self.critical
        )

    def is_warning(self):
        return self.current > self.maximum

    def is_critical(self):
        return self.current > self.critical


def get_sensors():
    """ Detect and return a list of Sensor objects """
    import sensors
    found_sensors = list()

    def get_subfeature_value(feature, subfeature_type):
        subfeature = chip.get_subfeature(feature, subfeature_type)
        if subfeature:
            return chip.get_value(subfeature.number)

    for chip in sensors.get_detected_chips():
        for feature in chip.get_features():
            if feature.type == sensors.FEATURE_TEMP:
                try:
                    name = chip.get_label(feature)
                    max = get_subfeature_value(feature, sensors.SUBFEATURE_TEMP_MAX)
                    current = get_subfeature_value(feature, sensors.SUBFEATURE_TEMP_INPUT)
                    critical = get_subfeature_value(feature, sensors.SUBFEATURE_TEMP_CRIT)
                    if critical:
                        found_sensors.append(Sensor(name=name, current=current, maximum=max, critical=critical))
                except sensors.SensorsException:
                    continue
    return found_sensors


class Temperature(IntervalModule, ColorRangeModule):
    """
    Shows CPU temperature of Intel processors.

    AMD is currently not supported as they can only report a relative temperature, which is pretty useless.

    Requires `colour` module from PyPi

    .. rubric:: Modes of operation

    If lm_sensors_enabled is set to False, the module operates in default mode. This means that:
        * only the {temp} formatter is available
        * alert_temp is honored

    If lm_sensors_enabled is set to True, the module operates in lm_sensors mode. This means that:
        * pysensors must be installed (https://github.com/bastienleonard/pysensors)
        * CPU sensors are discovered dynamically (supporting a sensor per core and multiple CPUs)
        * alert_temp is ignored. The warning or critical values reported by the sensor are used instead (see urgent_on)

    .. rubric:: lm_sensors installation

    In order to take advantage of the lm_sensors library and tools, it must first be installed and configured.

    On Arch this is as simple as:

    .. code-block:: bash

        pacman -S lm_sensors


    On Ubuntu:

    .. code-block:: bash

        sudo apt-get update && sudo apt-get install lm-sensors libsensors4-dev


    The Arch Wiki has a good page on the library - https://wiki.archlinux.org/index.php/lm_sensors

    .. rubric:: lm_sensors_mode formatters

    When ``lm_sensors_enabled`` is True the formatters are created dynamically. In order to discover the formatters that
    are available, it is best to run the sensors command:

    .. code-block:: bash

        ⇒ sensors
        coretemp-isa-0000
        Adapter: ISA adapter
        Physical id 0:  +48.0°C  (high = +80.0°C, crit = +99.0°C)
        Core 0:         +48.0°C  (high = +80.0°C, crit = +99.0°C)
        Core 1:         +46.0°C  (high = +80.0°C, crit = +99.0°C)
        Core 2:         +43.0°C  (high = +80.0°C, crit = +99.0°C)
        Core 3:         +47.0°C  (high = +80.0°C, crit = +99.0°C)

    The module replaces spaces in sensor names with underscores, therefore from the above output we can
    identify the following sensor formatters:

    * Physical_id_0
    * Core_0
    * Core_1
    * Core_2
    * Core_3

    For each sensor a vertical bar is also generated. In this example we would also have the following bars:

    * Physical_id_0_bar
    * Core_0_bar
    * Core_1_bar
    * Core_2_bar
    * Core_3_bar

    Thus, this format string would be valid: "{Physical_id_0}°C {Core_0_bar}{Core_1_bar}{Core_2_bar}{Core_3_bar}"

    .. rubric:: Pango Markup and lm_sensors_mode

    When Pango Markup is enabled and ``dynamic_color`` is True, each sensor's formatter color is displayed independently.
    The color is determined by the proximity of the sensors current value to it's critical value.

    .. rubric:: Example Configuration

    Here is an example configuration based on the sensor values discovered above:

    .. code-block:: python

        status.register("temp",
                        format="{Physical_id_0}°C {Core_0_bar}{Core_1_bar}{Core_2_bar}{Core_3_bar}",
                        hints={"markup": "pango"},
                        lm_sensors_enabled=True,
                        dynamic_color=True)
    """

    settings = (
        ("format",
         "format string used for output. {temp} is the temperature in degrees celsius"),
        ('display_if', 'snippet that gets evaluated. if true, displays the module output'),
        ('lm_sensors_enabled', 'whether or not lm_sensors should be used for obtaining CPU temperature information'),
        ('urgent_on', 'whether to flag as urgent when temperature exceeds urgent value or critical value '
                      '(requires lm_sensors_enabled)'),
        ('dynamic_color', 'whether to set the color dynamically (overrides alert_color)'),
        "color",
        "file",
        "alert_temp",
        "alert_color",
    )
    format = "{temp} °C"
    color = "#FFFFFF"
    file = "/sys/class/thermal/thermal_zone0/temp"
    alert_temp = 90
    alert_color = "#FF0000"
    display_if = 'True'

    lm_sensors_enabled = False
    dynamic_color = False
    urgent_on = 'warning'

    def init(self):
        self.pango_enabled = self.hints.get("markup", False) and self.hints["markup"] == "pango"
        self.colors = self.get_hex_color_range(self.start_color, self.end_color, 100)

    def run(self):
        if eval(self.display_if):
            if self.lm_sensors_enabled:
                self.output = self.get_output_sensors()
            else:
                self.output = self.get_output_original()

    def get_output_original(self):
        """
        Build the output the original way. Requires no third party libraries.
        """
        with open(self.file, "r") as f:
            temp = float(f.read().strip()) / 1000

        if self.dynamic_color:
            perc = int(self.percentage(int(temp), self.alert_temp))
            color = self.get_colour(perc)
        else:
            color = self.color if temp < self.alert_temp else self.alert_color
        return {
            "full_text": self.format.format(temp=temp),
            "color": color,
        }

    def get_output_sensors(self):
        """
        Build the output using lm_sensors. Requires sensors Python module (see docs).
        """
        data = dict()
        found_sensors = get_sensors()
        if len(found_sensors) == 0:
            raise Exception("No sensors detected! "
                            "Ensure lm-sensors is installed and check the output of the `sensors` command.")
        for sensor in found_sensors:
            data[sensor.name] = self.format_sensor(sensor)
            data["{}_bar".format(sensor.name)] = self.format_sensor_bar(sensor)
        data['temp'] = max((s.current for s in found_sensors))
        return {
            'full_text': self.format.format(**data),
            'urgent': self.get_urgent(found_sensors),
            'color': self.color if not self.dynamic_color else None,
        }

    def get_urgent(self, sensors):
        """ Determine if any sensors should set the urgent flag. """
        if self.urgent_on not in ('warning', 'critical'):
            raise Exception("urgent_on must be one of (warning, critical)")
        for sensor in sensors:
            if self.urgent_on == 'warning' and sensor.is_warning():
                return True
            elif self.urgent_on == 'critical' and sensor.is_critical():
                return True
        return False

    def format_sensor(self, sensor):
        """ Format a sensor value. If pango is enabled color is per sensor. """
        current_val = sensor.current
        if self.pango_enabled:
            percentage = self.percentage(sensor.current, sensor.critical)
            if self.dynamic_color:
                color = self.get_colour(percentage)
                return self.format_pango(color, current_val)
        return current_val

    def format_sensor_bar(self, sensor):
        """ Build and format a sensor bar. If pango is enabled bar color is per sensor."""
        percentage = self.percentage(sensor.current, sensor.critical)
        bar = make_vertical_bar(int(percentage))
        if self.pango_enabled:
            if self.dynamic_color:
                color = self.get_colour(percentage)
                return self.format_pango(color, bar)
        return bar

    def format_pango(self, color, value):
        return '<span color="{}">{}</span>'.format(color, value)

    def get_colour(self, percentage):
        index = -1 if int(percentage) > len(self.colors) - 1 else int(percentage)
        return self.colors[index]

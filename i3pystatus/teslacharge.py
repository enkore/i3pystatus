from tesla_api import TeslaApiClient
from i3pystatus import IntervalModule


class TeslaCharge(IntervalModule):
    """
    Displays the current charge/range of your Tesla vehicle. There is a ton of
    data that could be displayed, so read this module to see the full list of
    datapoints that can be displayed.
    Requires: tesla_api
    """

    settings = (
        ("email", "Email address used to login to your Tesla account."),
        ("password", "Password for accessing your Tesla account."),
        ("units", "Miles (default) or km"),
        ("interval", "Poll frequency. Polling too often can drain the battery"),
        ("format_with_charge", "Display format while car is charging"),
        ("format_without_charge", "Display format while car is not charging")
    )
    required = ("email", "password")
    units = "miles"
    conversion_factor = 0.62137119
    charge_complete = "#00FF00"  # green
    charging = "#FFFF00"         # yellow
    offline_color = "#FF0000"    # red
    interval = 900
    charging_icon = '⚡'
    disconnect_icon = ''
    format_with_charge = "{name}: {charge_state_icon}{charge_rate} {battery_level}%/{charge_limit_soc}% ({battery_range})"
    format_without_charge = "{name}: {battery_level}%/{charge_limit_soc}% ({battery_range})"

    def run(self):
        # Setup Tesla API client
        tclient = TeslaApiClient(self.email, self.password)
        vehicles = tclient.list_vehicles()
        # Currently, only one vehicle is supported. It would be nice to be
        # able to click through multipe vehicles.
        thisvehicle = vehicles[0]
        display_name = thisvehicle.display_name

        # If vehicle is offline, do not bother grabbing info
        if thisvehicle.state != 'online':
            self.output = {
                "full_text": "%s: %s" % (display_name, thisvehicle.state),
                "color": self.offline_color
            }
        else:
            charge_info = vehicles[0].charge.get_state()

            # Miles or meters?
            if self.units != "miles":
                battery_range = charge_info['battery_range'] * self.conversion_factor
                charge_rate = charge_info['charge_rate'] * self.conversion_factor
            else:
                battery_range = charge_info['battery_range']
                charge_rate = charge_info['charge_rate']

            # Set colors for charging status
            if charge_info['charging_state'] == 'Charging':
                color = self.charging
                charge_state_icon = self.charging_icon
            else:
                color = self.charge_complete
                charge_state_icon = self.disconnect_icon

            cdict = {
                "name": display_name,
                "charge_state_icon": charge_state_icon,
                "battery_level": charge_info['battery_level'],
                "battery_range": "%s %s" % (battery_range, self.units),
                "battery_heater_on": charge_info['battery_heater_on'],
                "charge_current_request": charge_info['charge_current_request'],
                "charge_current_request_max": charge_info['charge_current_request_max'],
                "charge_enable_request": charge_info['charge_enable_request'],
                "charge_energy_added": charge_info['charge_energy_added'],
                "charge_limit_soc": charge_info['charge_limit_soc'],
                "charge_limit_soc_max": charge_info['charge_limit_soc_max'],
                "charge_limit_soc_min": charge_info['charge_limit_soc_min'],
                "charge_limit_soc_std": charge_info['charge_limit_soc_std'],
                "charge_miles_added_ideal": charge_info['charge_miles_added_ideal'],
                "charge_miles_added_rated": charge_info['charge_miles_added_rated'],
                "charge_port_cold_weather_mode": charge_info['charge_port_cold_weather_mode'],
                "charge_port_door_open": charge_info['charge_port_door_open'],
                "charge_port_latch": charge_info['charge_port_latch'],
                "charge_rate": "%s%s/hr" % (charge_rate, self.units),
                "charge_to_max_range": charge_info['charge_to_max_range'],
                "charger_actual_current": charge_info['charger_actual_current'],
                "charger_phases": charge_info['charger_phases'],
                "charger_pilot_current": charge_info['charger_pilot_current'],
                "charger_power": charge_info['charger_power'],
                "charger_voltage": charge_info['charger_voltage'],
                "charging_state": charge_info['charging_state'],
                "conn_charge_cable": charge_info['conn_charge_cable'],
                "est_battery_range": charge_info['est_battery_range'],
                "fast_charger_brand": charge_info['fast_charger_brand'],
                "fast_charger_present": charge_info['fast_charger_present'],
                "fast_charger_type": charge_info['fast_charger_type'],
                "ideal_battery_range": charge_info['ideal_battery_range'],
                "managed_charging_active": charge_info['managed_charging_active'],
                "managed_charging_start_time": charge_info['managed_charging_start_time'],
                "managed_charging_user_canceled": charge_info['managed_charging_user_canceled'],
                "max_range_charge_counter": charge_info['max_range_charge_counter'],
                "minutes_to_full_charge": charge_info['minutes_to_full_charge'],
                "not_enough_power_to_heat": charge_info['not_enough_power_to_heat'],
                "scheduled_charging_pending": charge_info['scheduled_charging_pending'],
                "scheduled_charging_start_time": charge_info['scheduled_charging_start_time'],
                "time_to_full_charge": charge_info['time_to_full_charge'],
                "timestamp": charge_info['timestamp'],
                "trip_charging": charge_info['trip_charging'],
                "usable_battery_level": charge_info['usable_battery_level'],
                "user_charge_enable_request": charge_info['user_charge_enable_request']
            }

            if charge_info['charging_state'] == 'Charging':
                self.output = {
                    "full_text": self.format_with_charge.format(**cdict),
                    "color": color
                }
            else:
                self.output = {
                    "full_text": self.format_without_charge.format(**cdict),
                    "color": color
                }

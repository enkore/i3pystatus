from enum import IntEnum
from json import JSONDecodeError, loads
from i3pystatus import IntervalModule
from i3pystatus.core.command import run_through_shell
from i3pystatus.core.color import ColorRangeModule


class Buds(IntervalModule, ColorRangeModule):
    earbuds_binary = "earbuds"

    """
    Displays information about Galaxy Buds devices

    Requires the earbuds tool from https://github.com/JojiiOfficial/LiveBudsCli

    .. rubric :: Available formatters
    * {amb} Displays the current ambient sound control status.
    * {anc} Displays the current active noise control status.
    * {battery} Displays combined battery level for left and right.
        If both are at the same level, it simply returns the battery level.
        If they have different battery levels, it returns both levels, separated
        by space.
    * `{left_battery}` Displays the left bud battery level.
    * `{right_battery}` Displays the right bud battery level.
    * `{battery_case} Displays the case battery level, if one of the buds is on the case.
    * `{device_model}` The model of the device.
    * `{placement_left}` A placement indicator for the left bud, if it's on the (C)ase, (I)dle or being (W)ear.
    * `{placement_right}` A placement indicator for the right bud, if it's on the (C)ase, (I)dle or being (W)ear.
    """

    settings = (
        ("format", "Format string used for output"),
        ("interval", "Interval to run the module"),
        ("hide_no_device", "Hide the output if no device is connected"),
        ("connected_color", "Output color for when the device is connected"),
        ("disconnected_color", "Output color for when the device is disconnected"),
        ("dynamic_color", "Output color based on battery level. Overrides connected_color"),
        ("start_color", "Hex or English name for start of color range, eg '#00FF00' or 'green'"),
        ("end_color", "Hex or English name for end of color range, eg '#FF0000' or 'red'")
    )

    format = "{device_model} L{placement_left}{battery}R{placement_right}{battery_case}{amb}{anc}"
    hide_no_device = False
    battery_limit = 100

    connected_color = "#00FF00"
    disconnected_color = "#FF0000"
    dynamic_color = True
    colors = []

    on_leftclick = 'toggle_anc'
    on_rightclick = 'toggle_amb'
    on_doubleleftclick = 'connect'
    on_doublerightclick = 'disconnect'

    def init(self):
        if not self.dynamic_color:
            self.end_color = self.start_color = self.connected_color
        # battery discharges from battery_limit to 0
        self.colors = self.get_hex_color_range(self.end_color, self.start_color, self.battery_limit)

    def run(self):
        try:
            status = loads(run_through_shell(f"{self.earbuds_binary} status -o json -q").out)
        except JSONDecodeError:
            self.output = None
        else:
            payload = status.get("payload")
            if payload:
                amb = payload.get("ambient_sound_enabled")
                anc = payload.get("noise_reduction")
                left_battery = payload.get("batt_left")
                right_battery = payload.get("batt_right")
                placement_left = payload.get("placement_left")
                placement_right = payload.get("placement_right")

                fdict = {
                    "amb": " AMB" if amb else "",
                    "anc": " ANC" if anc else "",
                    "battery": f"{left_battery} {right_battery}" if left_battery != right_battery else left_battery,
                    "left_battery": left_battery,
                    "right_battery": right_battery,
                    "battery_case":
                        f' {payload.get("batt_case")}C' if placement_left == BudsPlacementStatus.case
                        or placement_right == BudsPlacementStatus.case else "",
                    "device_model": payload.get("model"),
                    "placement_left": self.translate_placement(placement_left),
                    "placement_right": self.translate_placement(placement_right),
                }

                color = self.get_gradient(
                    left_battery if left_battery < right_battery else right_battery,
                    self.colors,
                    self.battery_limit)

                self.output = {
                    "full_text": self.format.format(**fdict),
                    "color": color if self.dynamic_color else self.connected_color
                }

                return payload
            else:
                if not self.hide_no_device:
                    self.output = {
                        "full_text": "Disconnected",
                        "color": self.disconnected_color
                    }
                else:
                    self.output = None

        return

    def connect(self):
        run_through_shell(f"{self.earbuds_binary} connect")

    def disconnect(self):
        run_through_shell(f"{self.earbuds_binary} disconnect")

    def toggle_amb(self):
        payload = self.run()
        if payload:
            amb = payload.get("ambient_sound_enabled")
            if amb:
                run_through_shell("earbuds set ambientsound 0")
            else:
                run_through_shell("earbuds set ambientsound 1")

    def toggle_anc(self):
        payload = self.run()
        if payload:
            anc = payload.get("noise_reduction")
            if anc:
                run_through_shell("earbuds set anc false")
            else:
                run_through_shell("earbuds set anc true")

    @staticmethod
    def translate_placement(placement):
        mapping = {
            BudsPlacementStatus.wearing.value: "W",
            BudsPlacementStatus.idle.value: "I",
            BudsPlacementStatus.case.value: "C",
        }
        return mapping.get(placement, "?")


class BudsPlacementStatus(IntEnum):
    wearing = 1
    idle = 2
    case = 3

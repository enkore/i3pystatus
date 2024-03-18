import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.buds import Buds, BudsEqualizer, BudsPlacementStatus


class TestBuds(unittest.TestCase):
    def setUp(self):
        self.buds = Buds()
        with open('test_buds.json', 'rb') as file:
            self.payload = json.load(file)

    @patch('i3pystatus.buds.run_through_shell')
    def test_run_device_connected(self, mock_run):
        # Setup: Use json.dumps as we expect JSON
        payload = self.payload.get('connected_payload')
        mock_run.return_value.out = json.dumps(payload)

        # Action: Call run() and save return for comparison
        buds_run_return = self.buds.run()

        # Verify: Assert called with right params
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} status -o json -q")

        expected_output = {
            "full_text": "Buds2 LW53 48RW",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Assert correct output
        self.assertEqual(self.buds.output, expected_output)
        # Verify: run() return is equal to payload
        self.assertDictEqual(payload.get('payload'), buds_run_return)

    @patch('i3pystatus.buds.run_through_shell')
    def test_run_device_disconnected(self, mock_run):
        # Setup: Use json.dumps as we expect JSON
        mock_run.return_value.out = json.dumps(self.payload.get('disconnected_payload'))

        # Action: Call run() and save return for comparison
        buds_run_return = self.buds.run()

        # Verify: Assert called with right params
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} status -o json -q")

        expected_output = {
            "full_text": "Disconnected",
            "color": self.buds.disconnected_color
        }

        # Verify: Assert correct output
        self.assertEqual(self.buds.output, expected_output)
        # Verify: run() return should be none
        self.assertIsNone(buds_run_return)

    @patch('i3pystatus.buds.run_through_shell')
    def test_toggle_amb(self, mock_run):
        # Setup: AMB is initially disabled
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['ambient_sound_enabled'] = False

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Toggle AMB
        self.buds.toggle_amb()

        # Verify: The correct command is sent to enable AMB
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} set ambientsound 1")

        # Setup: Change the payload again to update the AMB status
        modified_payload['payload']['ambient_sound_enabled'] = True
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run again to update output
        self.buds.run()

        # Verify: The output correctly displays AMB is enabled
        expected_output = {
            "full_text": "Buds2 LW53 48RW AMB",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(self.buds.output, expected_output)

        # Action: Toggle AMB again
        self.buds.toggle_amb()

        # Verify: The correct command is sent to disable AMB this time
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} set ambientsound 0")

        # Setup: Change the payload one last time to update the AMB status
        modified_payload['payload']['ambient_sound_enabled'] = False
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run again to update output
        self.buds.run()

        # Verify: The output correctly displays AMB is disabled
        expected_output = {
            "full_text": "Buds2 LW53 48RW",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_toggle_anc(self, mock_run):
        # Setup: ANC is initially disabled
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['noise_reduction'] = False

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Toggle ANC
        self.buds.toggle_anc()

        # Verify: The correct command is sent to enable ANC
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} set anc true")

        # Setup: Change the payload again to update the ANC status
        modified_payload['payload']['noise_reduction'] = True
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run again to update output
        self.buds.run()

        # Verify: The output correctly displays ANC is enabled
        expected_output = {
            "full_text": "Buds2 LW53 48RW ANC",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(self.buds.output, expected_output)

        # Action: Toggle ANC again
        self.buds.toggle_anc()

        # Verify: The correct command is sent to disable ANC this time
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} set anc false")

        # Setup: Change the payload one last time to update the ANC status
        modified_payload['payload']['noise_reduction'] = False
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run again to update output
        self.buds.run()

        # Verify: The output correctly displays ANC is disabled
        expected_output = {
            "full_text": "Buds2 LW53 48RW",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_combined_battery(self, mock_run):
        # Setup: Equal left and right battery value
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() to update the output
        self.buds.run()

        expected_output = {
            "full_text": "Buds2 LW48RW",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(self.buds.output, expected_output)

        # Setup: Different left and right battery value
        mock_run.return_value.out = json.dumps(self.payload.get('connected_payload'))

        # Action: Call run() again to update the output
        self.buds.run()

        expected_output = {
            "full_text": "Buds2 LW53 48RW",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_connect(self, mock_run):
        # Action: Call connect
        self.buds.connect()

        # Verify: The correct command is sent to connect
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} connect")

    @patch('i3pystatus.buds.run_through_shell')
    def test_disconnect(self, mock_run):
        # Action: Call disconnect
        self.buds.disconnect()

        # Verify: The correct command is sent to disconnect
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} disconnect")

    @patch('i3pystatus.buds.run_through_shell')
    def test_restart_daemin(self, mock_run):
        # Action: Call restart_daemon
        self.buds.restart_daemon()

        # Verify: The correct command is sent to restart the daemon
        mock_run.assert_called_with(f"{self.buds.earbuds_binary} -kd")

    def run_placement_helper(self, mock_run, placement_left, placement_right, case_battery, expected_display):
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['placement_left'] = placement_left
        modified_payload['payload']['placement_right'] = placement_right
        if case_battery is not None:
            modified_payload['payload']['batt_case'] = case_battery
        mock_run.return_value.out = json.dumps(modified_payload)

        self.buds.run()

        expected_output = {
            "full_text": expected_display,
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }
        self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_placement_wearing(self, mock_run):
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.wearing.value,
            BudsPlacementStatus.wearing.value,
            None,
            "Buds2 LW53 48RW"
        )

    @patch('i3pystatus.buds.run_through_shell')
    def test_placement_idle(self, mock_run):
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.idle.value,
            BudsPlacementStatus.idle.value,
            None,
            "Buds2 LI53 48RI"
        )

    @patch('i3pystatus.buds.run_through_shell')
    def test_placement_case_with_battery(self, mock_run):
        # Verify: Case battery is returned if a bud is on the case
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.case.value,
            BudsPlacementStatus.case.value,
            88,
            "Buds2 LC53 48RC 88C"
        )

    @patch('i3pystatus.buds.run_through_shell')
    def test_battery_level_dynamic_color(self, mock_run):
        # Setup: Build the colors array independently of our class
        colors = ColorRangeModule.get_hex_color_range(
            self.buds.end_color,
            self.buds.start_color,
            self.buds.battery_limit
        )
        modified_payload = deepcopy(self.payload.get('connected_payload'))

        for battery_level in range(0, self.buds.battery_limit + 1):
            # Setup: Make both levels equal
            modified_payload['payload']['batt_left'] = battery_level
            modified_payload['payload']['batt_right'] = battery_level
            mock_run.return_value.out = json.dumps(modified_payload)

            # Action: Call run() again to update the output
            self.buds.run()

            expected_output = {
                "full_text": f"Buds2 LW{battery_level}RW",
                "color": self.buds.get_gradient(
                    battery_level,
                    colors,
                    self.buds.battery_limit
                )
            }

            self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_set_equalizer_direct(self, mock_run):
        for eq_setting in BudsEqualizer:
            with self.subTest(msg=f"Failed testing equalizer {eq_setting.name}", eq_setting=eq_setting):
                # Setup: Create a copy of the payload
                modified_payload = deepcopy(self.payload.get('connected_payload'))

                mock_run.return_value.out = json.dumps(modified_payload)

                # Action: Call the set function with each equalizer setting
                self.buds.equalizer_set(eq_setting)

                expected_command = f"{self.buds.earbuds_binary} set equalizer {eq_setting.name}"

                # Verify: Correct equalizer command is used
                mock_run.assert_called_with(expected_command)

                # Setup: Modify payload to verify output
                modified_payload['payload']['equalizer_type'] = eq_setting.value
                mock_run.return_value.out = json.dumps(modified_payload)

                # Action: Call run() again to update the output
                self.buds.run()

                expected_equalizer = f" {eq_setting.name.capitalize()}" if eq_setting.name != "off" else ""
                expected_output = {
                    "full_text": f"Buds2 LW53 48RW{expected_equalizer}",
                    "color": self.buds.get_gradient(
                        48,
                        self.buds.colors,
                        self.buds.battery_limit
                    )
                }

                # Verify: Output was updated with equalizer
                self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_increment_equalizer(self, mock_run):
        # Setup: Create a copy of the payload
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call the set to increment by one the equalizer setting
        self.buds.equalizer_set(+1)

        # Verify: Correct equalizer command is used
        expected_command = f"{self.buds.earbuds_binary} set equalizer {BudsEqualizer.bass.name}"
        mock_run.assert_called_with(expected_command)

        # Setup: Modify payload to verify output
        modified_payload['payload']['equalizer_type'] = BudsEqualizer.bass.value
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() again to update the output
        self.buds.run()

        expected_equalizer = f" {BudsEqualizer.bass.name.capitalize()}"
        expected_output = {
            "full_text": f"Buds2 LW53 48RW{expected_equalizer}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Output was updated with equalizer
        self.assertEqual(self.buds.output, expected_output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_decrement_equalizer_from_off(self, mock_run):
        # Setup: Create a copy of the payload
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call the set to decrement by one the equalizer setting
        self.buds.equalizer_set(-1)

        # Verify: Correct equalizer command is used
        expected_command = f"{self.buds.earbuds_binary} set equalizer {BudsEqualizer.treble.name}"
        mock_run.assert_called_with(expected_command)

        # Setup: Modify payload to verify output
        modified_payload['payload']['equalizer_type'] = BudsEqualizer.treble.value
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() again to update the output
        self.buds.run()

        expected_equalizer = f" {BudsEqualizer.treble.name.capitalize()}"
        expected_output = {
            "full_text": f"Buds2 LW53 48RW{expected_equalizer}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Output was updated with equalizer
        self.assertEqual(self.buds.output, expected_output)

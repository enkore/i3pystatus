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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Assert correct output
        self.assertEqual(expected_output, self.buds.output)
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
        self.assertEqual(expected_output, self.buds.output)
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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol} AMB",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(expected_output, self.buds.output)

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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(expected_output, self.buds.output)

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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol} ANC",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(expected_output, self.buds.output)

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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        self.assertEqual(expected_output, self.buds.output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_combined_battery(self, mock_run):
        # Setup: Equal left and right battery value
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() to update the output
        self.buds.run()

        expected_output = {
            "full_text": f"Buds2 L{self.buds.wearing_symbol}48R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

        # Setup: Different left and right battery value
        mock_run.return_value.out = json.dumps(self.payload.get('connected_payload'))

        # Action: Call run() again to update the output
        self.buds.run()

        expected_output = {
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_combined_battery_drift(self, mock_run):
        # Setup: Different battery level, should show combined, but the smaller level
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        modified_payload['payload']['batt_left'] -= self.buds.battery_drift_threshold

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() to update the output
        self.buds.run()

        expected_level = min(modified_payload['payload']['batt_left'], modified_payload['payload']['batt_right'])
        expected_output = {
            # Verify: The level should be the smallest one
            "full_text":
                f"Buds2 L{self.buds.wearing_symbol}{expected_level}R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                expected_level,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

        # Setup: One battery is at level 0, should show the one still with some battery level
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = 0
        modified_payload['payload']['batt_right'] = 0 + self.buds.battery_drift_threshold

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() again to update the output
        self.buds.run()

        expected_level = max(modified_payload['payload']['batt_left'], modified_payload['payload']['batt_right'])
        expected_output = {
            # Verify: The level should be the biggest one
            "full_text":
                f"Buds2 L{self.buds.wearing_symbol}{expected_level}R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                expected_level,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

        # Setup: Different battery level, but bigger than threshold, should show both levels
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        modified_payload['payload']['batt_left'] -= self.buds.battery_drift_threshold + 1

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() to update the output
        self.buds.run()

        expected_level = min(modified_payload['payload']['batt_left'], modified_payload['payload']['batt_right'])
        expected_output = {
            # Verify: The level should be the smallest one
            "full_text":
                f"Buds2 L{self.buds.wearing_symbol}{modified_payload['payload']['batt_left']} "
                f"{modified_payload['payload']['batt_right']}R{self.buds.wearing_symbol}",
            "color": self.buds.get_gradient(
                expected_level,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_combined_battery_drift_case(self, mock_run):
        # Setup: Change status of one buds to be on the case, should show both regardless of drift or not
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        modified_payload['payload']['placement_left'] = BudsPlacementStatus.case

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() to update the output
        self.buds.run()

        expected_output = {
            "full_text": f"Buds2 L{self.buds.case_symbol}48 48R{self.buds.wearing_symbol} "
                         f"88{self.buds.battery_case_symbol}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

        # Setup: Change status of one buds to be on the case, should show both regardless of drift or not
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        # Action: Introduce drift
        modified_payload['payload']['batt_left'] -= self.buds.battery_drift_threshold + 1
        modified_payload['payload']['placement_left'] = BudsPlacementStatus.case

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() to update the output
        self.buds.run()

        expected_output = {
            "full_text": f"Buds2 L{self.buds.case_symbol}44 48R{self.buds.wearing_symbol} "
                         f"88{self.buds.battery_case_symbol}",
            "color": self.buds.get_gradient(
                44,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: The output correctly displays combined battery status
        self.assertEqual(expected_output, self.buds.output)

    @patch('i3pystatus.buds.DesktopNotification')
    @patch('i3pystatus.buds.run_through_shell')
    def test_drift_notification(self, mock_run, mock_notification):
        # Setup: We set drift, but one of the buds is on the case, should not notify
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        modified_payload['payload']['placement_left'] = BudsPlacementStatus.case
        # Action: Introduce drift
        modified_payload['payload']['batt_left'] += self.buds.battery_drift_threshold + 1

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run()
        self.buds.run()

        # Verify: Should not notify in this scenario
        mock_notification.assert_not_called()

        # Setup: We set a drift threshold smaller than the class and number of expected calls
        drift_threshold = self.buds.battery_drift_threshold - 1
        expected_calls = (self.buds.battery_drift_threshold * 2) - 1 - drift_threshold

        # Setup: We range from our threshold to class threshold * 2 + 1, so we can check all possible notifications
        for drift in range(drift_threshold, (self.buds.battery_drift_threshold * 2) + 1):
            with self.subTest(msg=f"Failed testing drift notification with drift: {drift}", drift=drift):
                # Setup: Set the battery level according the drift
                modified_payload = deepcopy(self.payload.get('connected_payload'))
                modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
                # Action: Introduce drift
                modified_payload['payload']['batt_left'] += drift

                mock_run.return_value.out = json.dumps(modified_payload)

                # Action: Call run()
                self.buds.run()

                if drift <= self.buds.battery_drift_threshold:
                    # Verify: Should not notify in this scenario
                    mock_notification.assert_not_called()
                elif self.buds.battery_drift_threshold < drift <= self.buds.battery_drift_threshold * 2:
                    # Verify: Notification should have been called with right arguments
                    expected_arguments = {
                        "title": "Buds",
                        "body": f"Battery drift occurred L{modified_payload['payload']['batt_left']} "
                                f"{modified_payload['payload']['batt_right']}R",
                        "icon": "battery",
                        "urgency": 1
                    }

                    mock_notification.assert_called_with(**expected_arguments)

                    # Verify: Make sure the notification was actually displayed
                    mock_notification.return_value.display.assert_called()
                elif drift > self.buds.battery_drift_threshold * 2:
                    # Verify: Notification should not be called after threshold * 2
                    mock_notification.assert_not_called()

        # Verify: Make sure we only had the expected number of notifications
        self.assertEqual(mock_notification.call_count, expected_calls)
        self.assertEqual(mock_notification.return_value.display.call_count, expected_calls)

    @patch('i3pystatus.buds.DesktopNotification')
    @patch('i3pystatus.buds.run_through_shell')
    def test_drift_case_notification(self, mock_run, mock_notification):
        # Setup: Both buds have same level and are on the case, should not notify
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        modified_payload['payload']['placement_left'] = BudsPlacementStatus.case
        modified_payload['payload']['placement_right'] = BudsPlacementStatus.case

        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run()
        self.buds.run()

        # Verify: Should not notify in this scenario
        mock_notification.assert_not_called()

        # Setup: Start with one battery level smaller than the other and on case
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        modified_payload['payload']['batt_left'] = modified_payload['payload']['batt_right']
        modified_payload['payload']['batt_left'] -= self.buds.battery_drift_threshold + 1
        modified_payload['payload']['placement_left'] = BudsPlacementStatus.case
        batt_left_level_start = modified_payload['payload']['batt_left']
        batt_left_level_end = modified_payload['payload']['batt_right']

        # Setup: Range from start to end + threshold + 2, so we can check all possible notifications
        for level in range(batt_left_level_start, (batt_left_level_end + self.buds.battery_drift_threshold + 2)):
            with self.subTest(msg=f"Failed testing drift case notification with level: {level}", level=level):
                # Action: Increase level
                modified_payload['payload']['batt_left'] = level

                mock_run.return_value.out = json.dumps(modified_payload)

                # Action: Call run()
                self.buds.run()

                if level < batt_left_level_end:
                    # Verify: Should not notify in this scenario
                    mock_notification.assert_not_called()
                elif level == batt_left_level_end:
                    # Verify: Notification should have been called with right arguments
                    expected_arguments = {
                        "title": "Buds",
                        "body": f"Battery level reached L{modified_payload['payload']['batt_left']} "
                                f"{modified_payload['payload']['batt_right']}R",
                        "icon": "battery",
                        "urgency": 1
                    }

                    mock_notification.assert_called_with(**expected_arguments)

                    # Verify: Make sure the notification was actually displayed
                    mock_notification.return_value.display.assert_called()

        # Verify: Make sure we only had one notification
        self.assertEqual(mock_notification.call_count, 1)
        self.assertEqual(mock_notification.return_value.display.call_count, 1)

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
        self.assertEqual(expected_output, self.buds.output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_placement_wearing(self, mock_run):
        # Setup: Test once with class defaults
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.wearing.value,
            BudsPlacementStatus.wearing.value,
            None,
            f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}"
        )

        # Setup: test again, this time changing the wearing symbol
        self.buds.wearing_symbol = "🦻"

        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.wearing.value,
            BudsPlacementStatus.wearing.value,
            None,
            f"Buds2 L🦻53 48R🦻"
        )

    @patch('i3pystatus.buds.run_through_shell')
    def test_placement_idle(self, mock_run):
        # Setup: Test once with class defaults
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.idle.value,
            BudsPlacementStatus.idle.value,
            None,
            f"Buds2 L{self.buds.idle_symbol}53 48R{self.buds.idle_symbol}"
        )

        # Setup: test again, this time changing the idle symbol
        self.buds.idle_symbol = "🛋️"

        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.idle.value,
            BudsPlacementStatus.idle.value,
            None,
            "Buds2 L🛋️53 48R🛋️"
        )

    @patch('i3pystatus.buds.run_through_shell')
    def test_placement_case_with_battery(self, mock_run):
        # Setup: Test once with class defaults

        # Verify: Case battery is returned if a bud is on the case
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.case.value,
            BudsPlacementStatus.case.value,
            88,
            f"Buds2 L{self.buds.case_symbol}53 48R{self.buds.case_symbol} "
            f"88{self.buds.battery_case_symbol}"
        )

        # Setup: test again, this time changing the symbols
        self.buds.case_symbol = "\u26a1"
        self.buds.battery_case_symbol = "🔋"

        # Verify: Case battery is returned if a bud is on the case
        self.run_placement_helper(
            mock_run,
            BudsPlacementStatus.case.value,
            BudsPlacementStatus.case.value,
            88,
            f"Buds2 L\u26a153 48R\u26a1 88{self.buds.battery_case_symbol}"
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
                "full_text": f"Buds2 L{self.buds.wearing_symbol}{battery_level}R{self.buds.wearing_symbol}",
                "color": self.buds.get_gradient(
                    battery_level,
                    colors,
                    self.buds.battery_limit
                )
            }

            self.assertEqual(expected_output, self.buds.output)

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
                    "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}{expected_equalizer}",
                    "color": self.buds.get_gradient(
                        48,
                        self.buds.colors,
                        self.buds.battery_limit
                    )
                }

                # Verify: Output was updated with equalizer
                self.assertEqual(expected_output, self.buds.output)

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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}{expected_equalizer}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Output was updated with equalizer
        self.assertEqual(expected_output, self.buds.output)

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
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}{expected_equalizer}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Output was updated with equalizer
        self.assertEqual(expected_output, self.buds.output)

    def run_touchpad_set(self, mock_run, setting_value):
        # Setup: Create a copy of the payload
        modified_payload = deepcopy(self.payload.get('connected_payload'))
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call the set with the appropriate setting
        self.buds.touchpad_set(f'{setting_value}')

        # Verify: Correct command to disable the touchpad is called
        expected_command = f"{self.buds.earbuds_binary} set touchpad {setting_value}"
        mock_run.assert_called_with(expected_command)

        # Setup: Modify the payload if we are disabling the touchpad
        if setting_value == 'false':
            modified_payload['payload']['tab_lock_status']['touch_an_hold_on'] = False
            modified_payload['payload']['tab_lock_status']['tap_on'] = False
        mock_run.return_value.out = json.dumps(modified_payload)

        # Action: Call run() again to update the output
        self.buds.run()

        # Setup:
        expected_output = {
            "full_text": f"Buds2 L{self.buds.wearing_symbol}53 48R{self.buds.wearing_symbol}"
                         f"{' TL' if setting_value == 'false' else ''}",
            "color": self.buds.get_gradient(
                48,
                self.buds.colors,
                self.buds.battery_limit
            )
        }

        # Verify: Output was updated with equalizer
        self.assertEqual(expected_output, self.buds.output)

    @patch('i3pystatus.buds.run_through_shell')
    def test_touchpad_disable(self, mock_run):
        self.run_touchpad_set(mock_run, "false")

    @patch('i3pystatus.buds.run_through_shell')
    def test_touchpad_enable(self, mock_run):
        self.run_touchpad_set(mock_run, "true")

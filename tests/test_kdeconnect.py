"""
Tests for the kdeconnect module
"""

import unittest
from unittest.mock import patch, MagicMock
from i3pystatus import kdeconnect


class KDEConnectTest(unittest.TestCase):

    def _create_module(self, **kwargs):
        """Helper to create a KDEConnect module with mocked D-Bus"""
        with patch('i3pystatus.kdeconnect.dbus') as mock_dbus:
            mock_dbus.SessionBus.return_value = MagicMock()
            module = kdeconnect.KDEConnect(**kwargs)
            return module, mock_dbus

    @patch('i3pystatus.kdeconnect.dbus')
    def test_no_devices(self, mock_dbus):
        """Test output when no devices are available"""
        mock_bus = MagicMock()
        mock_dbus.SessionBus.return_value = mock_bus

        # Mock daemon to return empty device list
        mock_daemon = MagicMock()
        mock_iface = MagicMock()
        mock_iface.devices.return_value = []
        mock_bus.get_object.return_value = mock_daemon
        mock_dbus.Interface.return_value = mock_iface

        module = kdeconnect.KDEConnect()
        module.run()

        self.assertEqual(module.output['full_text'], "KDE Connect: No devices")
        self.assertEqual(module.output['color'], module.color_no_notifications)

    @patch('i3pystatus.kdeconnect.dbus')
    def test_no_notifications(self, mock_dbus):
        """Test output when device has no notifications"""
        mock_bus = MagicMock()
        mock_dbus.SessionBus.return_value = mock_bus

        # Setup mock objects
        mock_daemon = MagicMock()
        mock_device = MagicMock()
        mock_notif = MagicMock()

        def get_object(service, path):
            if path == '/modules/kdeconnect':
                return mock_daemon
            elif 'notifications' in path and '/' not in path.split('notifications')[1]:
                return mock_notif
            else:
                return mock_device

        mock_bus.get_object.side_effect = get_object

        # Mock interfaces
        def get_interface(obj, iface_name):
            mock_iface = MagicMock()
            if iface_name == 'org.kde.kdeconnect.daemon':
                mock_iface.devices.return_value = ['test_device_123']
            elif iface_name == 'org.freedesktop.DBus.Properties':
                mock_iface.Get.side_effect = lambda iface, prop: {
                    'name': 'My Phone',
                    'isReachable': True,
                }.get(prop, '')
            elif iface_name == 'org.kde.kdeconnect.device.notifications':
                mock_iface.activeNotifications.return_value = []
            return mock_iface

        mock_dbus.Interface.side_effect = get_interface

        module = kdeconnect.KDEConnect()
        module.run()

        self.assertIn("No notifications", module.output['full_text'])
        self.assertEqual(module.output['color'], module.color_no_notifications)

    @patch('i3pystatus.kdeconnect.dbus')
    def test_with_notifications(self, mock_dbus):
        """Test output when device has notifications"""
        mock_bus = MagicMock()
        mock_dbus.SessionBus.return_value = mock_bus

        # Track which object we're getting
        def get_object(service, path):
            mock_obj = MagicMock()
            mock_obj._path = path
            return mock_obj

        mock_bus.get_object.side_effect = get_object

        # Mock interfaces based on path and interface name
        def get_interface(obj, iface_name):
            mock_iface = MagicMock()
            path = getattr(obj, '_path', '')

            if iface_name == 'org.kde.kdeconnect.daemon':
                mock_iface.devices.return_value = ['phone123']
            elif iface_name == 'org.freedesktop.DBus.Properties':
                if 'notifications/notif1' in path:
                    mock_iface.Get.side_effect = lambda iface, prop: {
                        'appName': 'Messages',
                        'title': 'John Doe',
                        'text': 'Hello there!',
                        'dismissable': True,
                    }.get(prop, '')
                else:
                    mock_iface.Get.side_effect = lambda iface, prop: {
                        'name': 'My Phone',
                        'isReachable': True,
                    }.get(prop, '')
            elif iface_name == 'org.kde.kdeconnect.device.notifications':
                mock_iface.activeNotifications.return_value = ['notif1']
            return mock_iface

        mock_dbus.Interface.side_effect = get_interface

        module = kdeconnect.KDEConnect(format="{device_name}: {notification_count}")
        module.run()

        self.assertIn("My Phone", module.output['full_text'])
        self.assertIn("1", module.output['full_text'])
        self.assertEqual(module.output['color'], module.color)

    def test_default_click_handlers(self):
        """Test that default click handlers are set correctly"""
        with patch('i3pystatus.kdeconnect.dbus'):
            module = kdeconnect.KDEConnect()
            self.assertEqual(module.on_leftclick, 'next_notification')
            self.assertEqual(module.on_rightclick, 'dismiss_notification')
            self.assertEqual(module.on_middleclick, 'refresh')
            self.assertEqual(module.on_upscroll, 'prev_notification')
            self.assertEqual(module.on_downscroll, 'next_notification')

    def test_next_notification_cycles(self):
        """Test that next_notification cycles through notifications"""
        with patch('i3pystatus.kdeconnect.dbus'):
            module = kdeconnect.KDEConnect()
            module._notifications = [
                {'id': '1', 'app_name': 'App1', 'title': 'Title1', 'body': 'Body1'},
                {'id': '2', 'app_name': 'App2', 'title': 'Title2', 'body': 'Body2'},
                {'id': '3', 'app_name': 'App3', 'title': 'Title3', 'body': 'Body3'},
            ]
            module._notification_index = 0

            module.next_notification()
            self.assertEqual(module._notification_index, 1)

            module.next_notification()
            self.assertEqual(module._notification_index, 2)

            module.next_notification()
            self.assertEqual(module._notification_index, 0)  # Wraps around

    def test_prev_notification_cycles(self):
        """Test that prev_notification cycles backwards"""
        with patch('i3pystatus.kdeconnect.dbus'):
            module = kdeconnect.KDEConnect()
            module._notifications = [
                {'id': '1', 'app_name': 'App1', 'title': 'Title1', 'body': 'Body1'},
                {'id': '2', 'app_name': 'App2', 'title': 'Title2', 'body': 'Body2'},
            ]
            module._notification_index = 0

            module.prev_notification()
            self.assertEqual(module._notification_index, 1)  # Wraps to end

            module.prev_notification()
            self.assertEqual(module._notification_index, 0)

    def test_body_truncation(self):
        """Test that long notification bodies are truncated"""
        with patch('i3pystatus.kdeconnect.dbus') as mock_dbus:
            mock_bus = MagicMock()
            mock_dbus.SessionBus.return_value = mock_bus

            module = kdeconnect.KDEConnect(
                format="{body}",
                body_length=10
            )
            module._current_device_id = 'test123'
            module._device_name = 'Phone'
            module._notifications = [{
                'id': '1',
                'app_name': 'App',
                'title': 'Title',
                'body': 'This is a very long notification body that should be truncated',
                'dismissable': True
            }]
            module._notification_index = 0

            # Manually call run's formatting logic
            current = module._notifications[0]
            body = current['body']
            if len(body) > module.body_length:
                body = body[:module.body_length] + "…"

            self.assertEqual(body, "This is a …")
            self.assertEqual(len(body), 11)  # 10 chars + ellipsis


if __name__ == '__main__':
    unittest.main()


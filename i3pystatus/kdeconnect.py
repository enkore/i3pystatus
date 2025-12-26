import dbus

from i3pystatus import IntervalModule, formatp


class KDEConnect(IntervalModule):
    """
    Displays notifications from your phone via KDE Connect.

    Requires KDE Connect to be installed and running, with a paired device.
    Requires ``python-dbus`` from your distro package manager, or
    ``dbus-python`` from PyPI.

    Left click cycles through notifications.
    Right click dismisses the current notification.
    Middle click refreshes the notification list.

    .. rubric:: Available formatters

    * ``{notification_count}`` — number of active notifications
    * ``{app_name}`` — app that sent the current notification
    * ``{title}`` — notification title
    * ``{body}`` — notification body text (may be truncated)
    * ``{device_name}`` — name of the connected phone
    * ``{device_id}`` — ID of the connected device

    .. rubric:: Available callbacks

    * ``next_notification`` — cycle to next notification
    * ``prev_notification`` — cycle to previous notification
    * ``dismiss_notification`` — dismiss current notification
    * ``dismiss_all`` — dismiss all notifications
    * ``refresh`` — force refresh notification list
    """

    settings = (
        ("format", "Format string for display"),
        ("format_no_notifications", "Format when no notifications"),
        ("device_id", "Specific device ID to monitor (None = first available)"),
        ("color", "Default text color"),
        ("color_no_notifications", "Color when no notifications"),
        ("body_length", "Max length of notification body to display"),
    )

    format = "{device_name}: {notification_count} notif"
    format_no_notifications = "{device_name}: No notifications"
    device_id = None
    color = "#FFFFFF"
    color_no_notifications = "#888888"
    body_length = 50
    interval = 5

    on_leftclick = "next_notification"
    on_rightclick = "dismiss_notification"
    on_middleclick = "refresh"
    on_upscroll = "prev_notification"
    on_downscroll = "next_notification"

    _notification_index = 0
    _notifications = []
    _device_name = ""
    _current_device_id = None

    def init(self):
        self._bus = dbus.SessionBus()

    def _get_kdeconnect_devices(self):
        """Get list of available KDE Connect device IDs"""
        try:
            daemon = self._bus.get_object(
                'org.kde.kdeconnect',
                '/modules/kdeconnect'
            )
            iface = dbus.Interface(daemon, 'org.kde.kdeconnect.daemon')
            return list(iface.devices())
        except dbus.exceptions.DBusException:
            return []

    def _get_device_name(self, device_id):
        """Get the friendly name of a device"""
        try:
            device = self._bus.get_object(
                'org.kde.kdeconnect',
                f'/modules/kdeconnect/devices/{device_id}'
            )
            props = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            return str(props.Get('org.kde.kdeconnect.device', 'name'))
        except dbus.exceptions.DBusException:
            return device_id

    def _is_device_reachable(self, device_id):
        """Check if device is currently reachable"""
        try:
            device = self._bus.get_object(
                'org.kde.kdeconnect',
                f'/modules/kdeconnect/devices/{device_id}'
            )
            props = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            return bool(props.Get('org.kde.kdeconnect.device', 'isReachable'))
        except dbus.exceptions.DBusException:
            return False

    def _get_notifications(self, device_id):
        """Get list of active notifications from device"""
        try:
            notif_path = f'/modules/kdeconnect/devices/{device_id}/notifications'
            notif_obj = self._bus.get_object('org.kde.kdeconnect', notif_path)
            notif_iface = dbus.Interface(
                notif_obj,
                'org.kde.kdeconnect.device.notifications'
            )
            notification_ids = list(notif_iface.activeNotifications())

            notifications = []
            for notif_id in notification_ids:
                try:
                    n_path = f'{notif_path}/{notif_id}'
                    n_obj = self._bus.get_object('org.kde.kdeconnect', n_path)
                    n_props = dbus.Interface(
                        n_obj,
                        'org.freedesktop.DBus.Properties'
                    )
                    n_iface = 'org.kde.kdeconnect.device.notifications.notification'
                    notifications.append({
                        'id': notif_id,
                        'app_name': str(n_props.Get(n_iface, 'appName')),
                        'title': str(n_props.Get(n_iface, 'title')),
                        'body': str(n_props.Get(n_iface, 'text')),
                        'dismissable': bool(n_props.Get(n_iface, 'dismissable')),
                    })
                except dbus.exceptions.DBusException:
                    continue

            return notifications
        except dbus.exceptions.DBusException:
            return []

    def _dismiss_notification(self, device_id, notif_id):
        """Dismiss a specific notification"""
        try:
            notif_path = f'/modules/kdeconnect/devices/{device_id}/notifications/{notif_id}'
            notif_obj = self._bus.get_object('org.kde.kdeconnect', notif_path)
            notif_iface = dbus.Interface(
                notif_obj,
                'org.kde.kdeconnect.device.notifications.notification'
            )
            notif_iface.dismiss()
            return True
        except dbus.exceptions.DBusException:
            return False

    def run(self):
        try:
            # Find device to use
            if self.device_id:
                self._current_device_id = self.device_id
            else:
                devices = self._get_kdeconnect_devices()
                # Find first reachable device
                for dev_id in devices:
                    if self._is_device_reachable(dev_id):
                        self._current_device_id = dev_id
                        break
                else:
                    self._current_device_id = devices[0] if devices else None

            if not self._current_device_id:
                self.output = {
                    "full_text": "KDE Connect: No devices",
                    "color": self.color_no_notifications,
                }
                return

            self._device_name = self._get_device_name(self._current_device_id)
            self._notifications = self._get_notifications(self._current_device_id)

            if not self._notifications:
                self.output = {
                    "full_text": formatp(self.format_no_notifications,
                                         device_name=self._device_name,
                                         device_id=self._current_device_id,
                                         notification_count=0),
                    "color": self.color_no_notifications,
                }
                return

            # Ensure index is valid
            self._notification_index = self._notification_index % len(self._notifications)
            current = self._notifications[self._notification_index]

            # Truncate body if needed
            body = current['body']
            if len(body) > self.body_length:
                body = body[:self.body_length] + "…"

            fdict = {
                "notification_count": len(self._notifications),
                "app_name": current['app_name'],
                "title": current['title'],
                "body": body,
                "device_name": self._device_name,
                "device_id": self._current_device_id,
            }

            self.output = {
                "full_text": formatp(self.format, **fdict),
                "color": self.color,
            }

        except dbus.exceptions.DBusException as e:
            self.output = {
                "full_text": f"KDE Connect: {e.get_dbus_message()}",
                "color": "#FF0000",
            }
        except Exception as e:
            self.output = {
                "full_text": f"KDE Connect: Error - {str(e)}",
                "color": "#FF0000",
            }

    def next_notification(self):
        """Cycle to next notification"""
        if self._notifications:
            self._notification_index = (self._notification_index + 1) % len(self._notifications)

    def prev_notification(self):
        """Cycle to previous notification"""
        if self._notifications:
            self._notification_index = (self._notification_index - 1) % len(self._notifications)

    def dismiss_notification(self):
        """Dismiss the current notification"""
        if self._notifications and self._current_device_id:
            current = self._notifications[self._notification_index]
            if current.get('dismissable', False):
                self._dismiss_notification(self._current_device_id, current['id'])
                self._notifications.pop(self._notification_index)
                if self._notifications:
                    self._notification_index = self._notification_index % len(self._notifications)
                else:
                    self._notification_index = 0

    def dismiss_all(self):
        """Dismiss all notifications"""
        if self._current_device_id:
            for notif in self._notifications[:]:
                if notif.get('dismissable', False):
                    self._dismiss_notification(self._current_device_id, notif['id'])
            self._notifications = []
            self._notification_index = 0

    def refresh(self):
        """Force refresh notification list"""
        self.run()


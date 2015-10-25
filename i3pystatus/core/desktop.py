class BaseDesktopNotification:
    """
    Class to display a desktop notification

    :param title: Title of the notification
    :param body: Body text of the notification, depending on the users system configuration HTML may be used, but is not recommended
    :param icon: A XDG icon name, see http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
    :param urgency: A value between 1 and 3 with 1 meaning low urgency and 3 high urgency.
    :param timeout: Timeout in seconds for the notification. Zero means it needs to be dismissed by the user.
    """

    def __init__(self, title, body, icon="dialog-information", urgency=1, timeout=0):
        self.title = title
        self.body = body
        self.icon = icon
        self.urgency = urgency
        self.timeout = timeout

    def display(self):
        """
        Display this notification

        :returns: boolean indicating success
        """
        return False


class DesktopNotification(BaseDesktopNotification):
    pass


try:
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify
except (ImportError, ValueError):
    pass
else:
    if not Notify.init("i3pystatus"):
        raise ImportError("Couldn't initialize libnotify")

    # List of some useful icon names:
    # battery, battery-caution, battery-low
    # …

    class DesktopNotification(DesktopNotification):
        URGENCY_LUT = (
            Notify.Urgency.LOW,
            Notify.Urgency.NORMAL,
            Notify.Urgency.CRITICAL,
        )

        def display(self):
            notification = Notify.Notification.new(self.title, self.body, self.icon)
            if self.timeout:
                notification.set_timeout(self.timeout)
            notification.set_urgency(self.URGENCY_LUT[self.urgency])
            return notification.show()



def display_notification(title, body, icon="dialog-information", urgency=1, timeout=0):
    """
    Displays a desktop notification

    :param title: Title of the notification
    :param body: Body text of the notification, depending on the users system configuration HTML may be used, but is not recommended
    :param icon: A XDG icon name, see http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
    :param urgency: A value between 1 and 3 with 1 meaning low urgency and 3 high urgency.
    :param timeout: Timeout in seconds for the notification. Zero means it needs to be dismissed by the user.
    :returns: boolean indicating success
    """
    return False

try:
    from gi.repository import Notify
except ImportError:
    pass
else:
    if not Notify.init("i3pystatus"):
        raise ImportError("Couldn't initialize libnotify")

    URGENCY_LUT = (
        Notify.Urgency.LOW,
        Notify.Urgency.NORMAL,
        Notify.Urgency.CRITICAL,
    )

    # List of some useful icon names:
    # battery, battery-caution, battery-low
    # …

    def display_notification(title, body, icon="dialog-information", urgency=1, timeout=0):
        notification = Notify.Notification.new(title, body, icon)
        if timeout:
            notification.set_timeout(timeout)
        notification.set_urgency(URGENCY_LUT[urgency])
        return notification.show()

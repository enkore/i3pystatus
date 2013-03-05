
from gi.repository import Notify

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

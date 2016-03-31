import time

from i3pystatus import IntervalModule
from i3pystatus.core.command import execute
from i3pystatus.core.util import TimeWrapper


class TimerState:
    stopped = 0
    running = 1
    overflow = 2


class Timer(IntervalModule):
    """
    Timer module to remind yourself that there probably is something else you
    should be doing right now.

    Main features include:

    - Set custom time interval with click events.
    - Different output formats triggered when remaining time is less than `x`
      seconds.
    - Execute custom python function or external command when timer overflows
      (or reaches zero depending on how you look at it).

    .. rubric:: Available formatters

    Time formatters are available to show the remaining time.
    These include ``%h``, ``%m``, ``%s``, ``%H``, ``%M``, ``%S``.
    See :py:class:`.TimeWrapper` for detailed description.

    The ``format_custom`` setting allows you to display different formats when
    certain amount of seconds is remaining.
    This setting accepts list of tuples which contain time in seconds,
    format string and color string each.
    See the default settings for an example:

    - ``(0, "+%M:%S", "#ffffff")`` - Use this format after overflow. White text
      with red background set by the urgent flag.
    - ``(60, "-%M:%S", "#ffa500")`` - Change color to orange in last minute.
    - ``(3600, "-%M:%S", "#00ff00")`` - Hide hour digits when remaining time is
      less than one hour.

    Only first matching rule is applied (if any).

    .. rubric:: Callbacks

    Module contains three mouse event callback methods:

    - :py:meth:`.start` - Default: Left click starts (or adds) 5 minute
      countdown.
    - :py:meth:`.increase` - Default: Upscroll/downscroll increase/decrease time
      by 1 minute.
    - :py:meth:`.reset` - Default: Right click resets timer.

    Two new event settings were added:

    - ``on_overflow`` - Executed when remaining time reaches zero.
    - ``on_reset`` - Executed when timer is reset but only if overflow occured.

    These settings accept either a python callable object or a string with shell
    command.
    Python callbacks should be non-blocking and without any arguments.

    Here is an example that plays a short sound file in 'loop' every 60 seconds
    until timer is reset.
    (``play`` is part of ``SoX`` - the Swiss Army knife of audio manipulation)

    ::

        on_overflow = "play -q /path/to/sound.mp3 pad 0 60 repeat -"
        on_reset = "pkill -SIGTERM -f 'play -q /path/to/sound.mp3 pad 0 60 repeat -'"

    """

    interval = 1

    on_leftclick = ["start", 300]
    on_rightclick = "reset"
    on_upscroll = ["increase", 60]
    on_downscroll = ["increase", -60]

    settings = (
        ("format", "Default format that is showed if no ``format_custom`` "
         "rules are matched."),
        ("format_stopped", "Format showed when timer is inactive."),
        "color",
        "color_stopped",
        "format_custom",
        ("overflow_urgent", "Set urgent flag on overflow."),
        "on_overflow",
        "on_reset",
    )

    format = '-%h:%M:%S'
    format_stopped = "T"
    color = "#00ff00"
    color_stopped = "#ffffff"
    format_custom = [
        (0, "+%M:%S", "#ffffff"),
        (60, "-%M:%S", "#ffa500"),
        (3600, "-%M:%S", "#00ff00"),
    ]
    overflow_urgent = True
    on_overflow = None
    on_reset = None

    def init(self):
        self.compare = 0
        self.state = TimerState.stopped
        if not self.format_custom:
            self.format_custom = []

    def run(self):
        if self.state is not TimerState.stopped:
            diff = self.compare - time.time()

            if diff < 0 and self.state is TimerState.running:
                self.state = TimerState.overflow
                if self.on_overflow:
                    if callable(self.on_overflow):
                        self.on_overflow()
                    else:
                        execute(self.on_overflow)

            fmt = self.format
            color = self.color
            for rule in self.format_custom:
                if diff < rule[0]:
                    fmt = rule[1]
                    color = rule[2]
                    break
            urgent = self.overflow_urgent and self.state is TimerState.overflow

            self.output = {
                "full_text": format(TimeWrapper(abs(diff), fmt)),
                "color": color,
                "urgent": urgent,
            }
        else:
            self.output = {
                "full_text": self.format_stopped,
                "color": self.color_stopped,
            }

    def start(self, seconds=300):
        """
        Starts timer.
        If timer is already running it will increase remaining time instead.

        :param int seconds: Initial time.
        """
        if self.state is TimerState.stopped:
            self.compare = time.time() + abs(seconds)
            self.state = TimerState.running
        elif self.state is TimerState.running:
            self.increase(seconds)

    def increase(self, seconds):
        """
        Change remainig time value.

        :param int seconds: Seconds to add. Negative value substracts from
         remaining time.
        """
        if self.state is TimerState.running:
            new_compare = self.compare + seconds
            if new_compare > time.time():
                self.compare = new_compare

    def reset(self):
        """
        Stop timer and execute ``on_reset`` if overflow occured.
        """
        if self.state is not TimerState.stopped:
            if self.on_reset and self.state is TimerState.overflow:
                if callable(self.on_reset):
                    self.on_reset()
                else:
                    execute(self.on_reset)
            self.state = TimerState.stopped

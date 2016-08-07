# -*- coding: utf-8 -*-
from threading import Thread
from i3pystatus import Module
import i3ipc


class Scratchpad(Module):
    """
    Display the amount of windows and indicate urgency hints on scratchpad (async).

    fork from scratchpad_async of py3status by cornerman

    Requires the PyPI package `i3ipc`.

    .. rubric:: Available formaters

    * `{number}`      — amount of windows on scratchpad

    @author jok
    @license BSD
    """

    settings = (
        ("format", "format string."),
        ("always_show", "whether the indicator should be shown if there are"
         " no scratchpad windows"),
        ("color_urgent", "color of urgent"),
        ("color", "text color"),
    )

    format = u"{number} ⌫"
    always_show = True
    color_urgent = "#900000"
    color = "#FFFFFF"

    def init(self):
        self.count = 0
        self.urgent = False

        t = Thread(target=self._listen)
        t.daemon = True
        t.start()

    def update_scratchpad_counter(self, conn, *args):
        cons = conn.get_tree().scratchpad().leaves()
        self.urgent = any(con for con in cons if con.urgent)
        self.count = len(cons)

        # output
        if self.urgent:
            color = self.color_urgent
        else:
            color = self.color

        if self.always_show or self.count > 0:
            full_text = self.format.format(number=self.count)
        else:
            full_text = ''

        self.output = {
            "full_text": full_text,
            "color": color,
        }

    def _listen(self):
        conn = i3ipc.Connection()
        self.update_scratchpad_counter(conn)

        conn.on('window::move', self.update_scratchpad_counter)
        conn.on('window::urgent', self.update_scratchpad_counter)
        conn.on('window::new', self.update_scratchpad_counter)
        conn.on('window::close', self.update_scratchpad_counter)

        conn.main()

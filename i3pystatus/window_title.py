# -*- coding: utf-8 -*-
from i3pystatus import Module
from threading import Thread
import i3ipc


class WindowTitle(Module):
    """
    Display the current window title with async update.
    Uses asynchronous update via i3 IPC events.
    Provides instant title update only when it required.

    fork from window_tile_async of py3status by Anon1234 https://github.com/Anon1234

    Requires the PyPI package `i3ipc`.

    .. rubric:: Available formaters

    * `{title}`      — title of current focused window
    * `{class_name}` - name of application class

    @author jok
    @license BSD
    """

    settings = (
        ("format", "format string."),
        ("always_show", "do not hide the title when it can be already visible"),
        ("empty_title", "string that will be shown instead of the title when the title is hidden"),
        ("max_width", "maximum width of title"),
        ("color", "text color"),
    )

    format = "{title}"
    always_show = False
    empty_title = ""
    max_width = 79
    color = "#FFFFFF"

    def init(self):
        self.title = self.empty_title
        self.output = {
            "full_text": self.title,
            "color": self.color,
        }

        # we are listening to i3 events in a separate thread
        t = Thread(target=self._loop)
        t.daemon = True
        t.start()

    def get_title(self, conn):
        tree = conn.get_tree()
        w = tree.find_focused()
        p = w.parent

        # don't show window title when the window already has means
        # to display it
        if (not self.always_show and
            (w.border == "normal" or w.type == "workspace" or
                (p.layout in ("stacked", "tabbed") and len(p.nodes) > 1))):
            return self.empty_title
        else:
            title = w.name
            class_name = w.window_class
            if len(title) > self.max_width:
                title = title[:self.max_width - 1] + "…"
            return self.format.format(title=title, class_name=class_name)

    def update_title(self, conn, e):
        # catch only focused window title updates
        title_changed = hasattr(e, "container") and e.container.focused

        # check if we need to update title due to changes
        # in the workspace layout
        layout_changed = (
            hasattr(e, "binding") and
            (e.binding.command.startswith("layout") or
             e.binding.command.startswith("move container") or
             e.binding.command.startswith("border"))
        )

        if title_changed or layout_changed:
            self.title = self.get_title(conn)
            self.update_display()

    def clear_title(self, *args):
        self.title = self.empty_title
        self.update_display()

    def update_display(self):
        self.output = {
            "full_text": self.title,
            "color": self.color,
        }

    def _loop(self):
        conn = i3ipc.Connection()
        self.title = self.get_title(conn)  # set title on startup
        self.update_display()

        # The order of following callbacks is important!
        # clears the title on empty ws
        conn.on('workspace::focus', self.clear_title)

        # clears the title when the last window on ws was closed
        conn.on("window::close", self.clear_title)

        # listens for events which can trigger the title update
        conn.on("window::title", self.update_title)
        conn.on("window::focus", self.update_title)

        conn.main()  # run the event loop

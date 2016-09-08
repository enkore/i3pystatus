import re
import subprocess

from i3pystatus import Module
from i3pystatus.core.color import ColorRangeModule
from i3pystatus.core.util import make_vertical_bar, make_bar
from .pulse import *


class PulseAudio(Module, ColorRangeModule):
    """
    Shows volume of default PulseAudio sink (output).

    - Requires amixer for toggling mute and incrementing/decrementing volume on scroll.
    - Depends on the PyPI colour module - https://pypi.python.org/pypi/colour/0.0.5

    .. rubric:: Available formatters

    * `{volume}` — volume in percent (0...100)
    * `{db}` — volume in decibels relative to 100 %, i.e. 100 % = 0 dB, 50 % = -18 dB, 0 % = -infinity dB
      (the literal value for -infinity is `-∞`)
    * `{muted}` — the value of one of the `muted` or `unmuted` settings
    * `{volume_bar}` — unicode bar showing volume
    """

    settings = (
        "format",
        ("format_muted", "optional format string to use when muted"),
        "muted", "unmuted",
        "color_muted", "color_unmuted",
        ("step", "percentage to increment volume on scroll"),
        ("bar_type", "type of volume bar. Allowed values are 'vertical' or 'horizontal'"),
        ("multi_colors", "whether or not to change the color from "
                         "'color_muted' to 'color_unmuted' based on volume percentage"),
        ("vertical_bar_width", "how many characters wide the vertical volume_bar should be")
    )

    muted = "M"
    unmuted = ""
    format = "♪: {volume}"
    format_muted = None
    currently_muted = False
    has_amixer = False
    color_muted = "#FF0000"
    color_unmuted = "#FFFFFF"

    step = 5
    multi_colors = False
    bar_type = 'vertical'
    vertical_bar_width = 2

    on_rightclick = "switch_mute"
    on_doubleleftclick = "change_sink"
    on_leftclick = "pavucontrol"
    on_upscroll = "increase_volume"
    on_downscroll = "decrease_volume"

    def init(self):
        """Creates context, when context is ready context_notify_cb is called"""
        # Wrap callback methods in appropriate ctypefunc instances so
        # that the Pulseaudio C API can call them
        self._context_notify_cb = pa_context_notify_cb_t(
            self.context_notify_cb)
        self._sink_info_cb = pa_sink_info_cb_t(self.sink_info_cb)
        self._update_cb = pa_context_subscribe_cb_t(self.update_cb)
        self._success_cb = pa_context_success_cb_t(self.success_cb)
        self._server_info_cb = pa_server_info_cb_t(self.server_info_cb)

        # Create the mainloop thread and set our context_notify_cb
        # method to be called when there's updates relating to the
        # connection to Pulseaudio
        _mainloop = pa_threaded_mainloop_new()
        _mainloop_api = pa_threaded_mainloop_get_api(_mainloop)
        context = pa_context_new(_mainloop_api, "i3pystatus_pulseaudio".encode("ascii"))

        pa_context_set_state_callback(context, self._context_notify_cb, None)
        pa_context_connect(context, None, 0, None)
        pa_threaded_mainloop_start(_mainloop)

        self.colors = self.get_hex_color_range(self.color_muted, self.color_unmuted, 100)
        self.sinks = []

    def request_update(self, context):
        """Requests a sink info update (sink_info_cb is called)"""
        pa_operation_unref(pa_context_get_sink_info_by_name(
            context, self.sink.encode(), self._sink_info_cb, None))

    def success_cb(self, context, success, userdata):
        pass

    @property
    def sink(self):
        self.sinks = subprocess.check_output(['pactl', 'list', 'short', 'sinks'],
                                             universal_newlines=True).splitlines()
        bestsink = None
        state = 'DEFAULT'
        for sink in self.sinks:
            attribs = sink.split()
            sink_state = attribs[-1]
            if sink_state == 'RUNNING':
                bestsink = attribs[1]
                state = 'RUNNING'
            elif sink_state in ('IDLE', 'SUSPENDED') and state == 'DEFAULT':
                bestsink = attribs[1]
        return bestsink

    def server_info_cb(self, context, server_info_p, userdata):
        """Retrieves the default sink and calls request_update"""
        server_info = server_info_p.contents
        self.request_update(context)

    def context_notify_cb(self, context, _):
        """Checks wether the context is ready

        -Queries server information (server_info_cb is called)
        -Subscribes to property changes on all sinks (update_cb is called)
        """
        state = pa_context_get_state(context)

        if state == PA_CONTEXT_READY:
            pa_operation_unref(
                pa_context_get_server_info(context, self._server_info_cb, None))

            pa_context_set_subscribe_callback(context, self._update_cb, None)

            pa_operation_unref(pa_context_subscribe(
                context, PA_SUBSCRIPTION_EVENT_CHANGE | PA_SUBSCRIPTION_MASK_SINK | PA_SUBSCRIPTION_MASK_SERVER, self._success_cb, None))

    def update_cb(self, context, t, idx, userdata):
        """A sink property changed, calls request_update"""

        if t & PA_SUBSCRIPTION_EVENT_FACILITY_MASK == PA_SUBSCRIPTION_EVENT_SERVER:
            pa_operation_unref(
                pa_context_get_server_info(context, self._server_info_cb, None))

        self.request_update(context)

    def sink_info_cb(self, context, sink_info_p, _, __):
        """Updates self.output"""
        if sink_info_p:
            sink_info = sink_info_p.contents
            volume_percent = round(100 * sink_info.volume.values[0] / 0x10000)
            volume_db = pa_sw_volume_to_dB(sink_info.volume.values[0])
            self.currently_muted = sink_info.mute

            if volume_db == float('-Infinity'):
                volume_db = "-∞"
            else:
                volume_db = int(volume_db)

            muted = self.muted if sink_info.mute else self.unmuted

            if self.multi_colors and not sink_info.mute:
                color = self.get_gradient(volume_percent, self.colors)
            else:
                color = self.color_muted if sink_info.mute else self.color_unmuted

            if muted and self.format_muted is not None:
                output_format = self.format_muted
            else:
                output_format = self.format

            if self.bar_type == 'vertical':
                volume_bar = make_vertical_bar(volume_percent, self.vertical_bar_width)
            elif self.bar_type == 'horizontal':
                volume_bar = make_bar(volume_percent)
            else:
                raise Exception("bar_type must be 'vertical' or 'horizontal'")

            self.output = {
                "color": color,
                "full_text": output_format.format(
                    muted=muted,
                    volume=volume_percent,
                    db=volume_db,
                    volume_bar=volume_bar),
            }

            self.send_output()

    def change_sink(self):
        curr_sink = self.sink
        sinks = list(s.split()[1] for s in self.sinks)
        next_sink = (sinks.index(curr_sink) + 1) % len(sinks)

        sink_inputs = subprocess.check_output("pacmd list-sink-inputs".split(),
                                              universal_newlines=True)
        for input_index in re.findall('index:\s+(\d+)', sink_inputs):
            command = "pacmd move-sink-input {} {}".format(input_index, sinks[next_sink])
            subprocess.call(command.split())
        subprocess.call("pacmd set-default-sink {}".format(sinks[next_sink]).split())

    def switch_mute(self):
        subprocess.call(['pactl', 'set-sink-mute', self.sink, "toggle"])

    def increase_volume(self):
        subprocess.call(['pactl', 'set-sink-volume', self.sink, "+%s%%" % self.step])

    def decrease_volume(self):
        subprocess.call(['pactl', 'set-sink-volume', self.sink, "-%s%%" % self.step])

# libpulseaudio in PyPI
from pulseaudio.lib_pulseaudio import *

from i3pystatus import Module

class PulseAudio(Module):
    """
    Shows volume of default PulseAudio sink (output).

    Requires libpulseaudio from PyPI. Based on http://freshfoo.com/blog/pulseaudio_monitoring
    """

    settings = (
        ("format", "{volume} is the current volume"),
    )

    format = "♪: {volume}"

    def init(self):
        # Wrap callback methods in appropriate ctypefunc instances so
        # that the Pulseaudio C API can call them
        self._context_notify_cb = pa_context_notify_cb_t(self.context_notify_cb)
        self._sink_info_cb = pa_sink_info_cb_t(self.sink_info_cb)
        self._update_cb = pa_context_subscribe_cb_t(self.update_cb)
        self._success_cb = pa_context_success_cb_t (self.success_cb)
        self._server_info_cb = pa_server_info_cb_t(self.server_info_cb)

        # Create the mainloop thread and set our context_notify_cb
        # method to be called when there's updates relating to the
        # connection to Pulseaudio
        _mainloop = pa_threaded_mainloop_new()
        _mainloop_api = pa_threaded_mainloop_get_api(_mainloop)
        context = pa_context_new(_mainloop_api, 'peak_demo'.encode("ascii"))

        pa_context_set_state_callback(context, self._context_notify_cb, None)
        pa_context_connect(context, None, 0, None)
        pa_threaded_mainloop_start(_mainloop)

    def request_update(self, context):
        pa_operation_unref(pa_context_get_sink_info_by_name(context, self.sink, self._sink_info_cb, None))

    def success_cb(self, context, success, userdata):
        pass

    def server_info_cb(self, context, server_info_p, userdata):
        server_info = server_info_p.contents

        self.sink = server_info.default_sink_name

        self.request_update(context)

    def context_notify_cb(self, context, _):
        state = pa_context_get_state(context)

        if state == PA_CONTEXT_READY:
            pa_operation_unref(pa_context_get_server_info(context, self._server_info_cb, None))

            pa_context_set_subscribe_callback(context, self._update_cb, None)

            # PA_SUBSCRIPTION_EVENT_CHANGE 
            # PA_SUBSCRIPTION_MASK_SOURCE_OUTPUT 
            pa_operation_unref(pa_context_subscribe(context, PA_SUBSCRIPTION_EVENT_CHANGE|PA_SUBSCRIPTION_MASK_SINK, self._success_cb, None))

    def update_cb(self, context, t, idx, userdata):
        """A sink property changed"""
        self.request_update(context)

    def sink_info_cb(self, context, sink_info_p, _, __):
        if sink_info_p:
            sink_info = sink_info_p.contents
            volume_percent = int(100 * sink_info.volume.values[0]/0x10000)

            self.output = {
                "full_text": self.format.format(volume=volume_percent),
            }

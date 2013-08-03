# generation commands
# h2xml.py -I $PWD -c -o pa.xml pulse/mainloop-api.h pulse/sample.h pulse/def.h pulse/operation.h pulse/context.h pulse/channelmap.h pulse/volume.h pulse/stream.h pulse/introspect.h pulse/subscribe.h pulse/scache.h pulse/version.h pulse/error.h pulse/xmalloc.h pulse/utf8.h pulse/thread-mainloop.h pulse/mainloop.h pulse/mainloop-signal.h pulse/util.h pulse/timeval.h
# xml2py.py -k efstd -o lib_pulseaudio.py -l 'pulse' -r '(pa|PA)_.+' pa.xml

from ctypes import *

_libraries = {}
_libraries['libpulse.so.0'] = CDLL('libpulse.so.0')
STRING = c_char_p
pa_volume_t = c_uint32
pa_channel_position_t = c_int
pa_usec_t = c_uint64
pa_channel_position_mask_t = c_uint64

PA_CONTEXT_AUTHORIZING = 2
PA_CONTEXT_CONNECTING = 1
PA_CONTEXT_FAILED = 5
PA_CONTEXT_NOAUTOSPAWN = 1
PA_CONTEXT_NOFAIL = 2
PA_CONTEXT_NOFLAGS = 0
PA_CONTEXT_READY = 4
PA_CONTEXT_SETTING_NAME = 3
PA_CONTEXT_TERMINATED = 6
PA_CONTEXT_UNCONNECTED = 0
PA_OK = 0
PA_OPERATION_CANCELLED = 2
PA_OPERATION_DONE = 1
PA_OPERATION_RUNNING = 0
PA_SUBSCRIPTION_EVENT_CHANGE = 16
PA_SUBSCRIPTION_MASK_SINK = 1

class pa_sink_port_info(Structure):
    pass
class pa_format_info(Structure):
    pass
class pa_context(Structure):
    pass
pa_context._fields_ = [
]
pa_context_notify_cb_t = CFUNCTYPE(None, POINTER(pa_context), c_void_p)
pa_context_success_cb_t = CFUNCTYPE(None, POINTER(pa_context), c_int, c_void_p)
class pa_proplist(Structure):
    pass
pa_context_event_cb_t = CFUNCTYPE(None, POINTER(pa_context), STRING, POINTER(pa_proplist), c_void_p)
class pa_mainloop_api(Structure):
    pass
pa_context_new = _libraries['libpulse.so.0'].pa_context_new
pa_context_new.restype = POINTER(pa_context)
pa_context_new.argtypes = [POINTER(pa_mainloop_api), STRING]
pa_context_new_with_proplist = _libraries['libpulse.so.0'].pa_context_new_with_proplist
pa_context_new_with_proplist.restype = POINTER(pa_context)
pa_context_new_with_proplist.argtypes = [POINTER(pa_mainloop_api), STRING, POINTER(pa_proplist)]
pa_context_unref = _libraries['libpulse.so.0'].pa_context_unref
pa_context_unref.restype = None
pa_context_unref.argtypes = [POINTER(pa_context)]
pa_context_ref = _libraries['libpulse.so.0'].pa_context_ref
pa_context_ref.restype = POINTER(pa_context)
pa_context_ref.argtypes = [POINTER(pa_context)]
pa_context_set_state_callback = _libraries['libpulse.so.0'].pa_context_set_state_callback
pa_context_set_state_callback.restype = None
pa_context_set_state_callback.argtypes = [POINTER(pa_context), pa_context_notify_cb_t, c_void_p]
pa_context_set_event_callback = _libraries['libpulse.so.0'].pa_context_set_event_callback
pa_context_set_event_callback.restype = None
pa_context_set_event_callback.argtypes = [POINTER(pa_context), pa_context_event_cb_t, c_void_p]
pa_context_errno = _libraries['libpulse.so.0'].pa_context_errno
pa_context_errno.restype = c_int
pa_context_errno.argtypes = [POINTER(pa_context)]
pa_context_is_pending = _libraries['libpulse.so.0'].pa_context_is_pending
pa_context_is_pending.restype = c_int
pa_context_is_pending.argtypes = [POINTER(pa_context)]

# values for enumeration 'pa_context_state'
pa_context_state = c_int # enum
pa_context_state_t = pa_context_state
pa_context_get_state = _libraries['libpulse.so.0'].pa_context_get_state
pa_context_get_state.restype = pa_context_state_t
pa_context_get_state.argtypes = [POINTER(pa_context)]

# values for enumeration 'pa_context_flags'
pa_context_flags = c_int # enum
pa_context_flags_t = pa_context_flags
class pa_spawn_api(Structure):
    _fields_ = [
        ('prefork', CFUNCTYPE(None)),
        ('postfork', CFUNCTYPE(None)),
        ('atfork', CFUNCTYPE(None)),
    ]

pa_context_connect = _libraries['libpulse.so.0'].pa_context_connect
pa_context_connect.restype = c_int
pa_context_connect.argtypes = [POINTER(pa_context), STRING, pa_context_flags_t, POINTER(pa_spawn_api)]
pa_context_disconnect = _libraries['libpulse.so.0'].pa_context_disconnect
pa_context_disconnect.restype = None
pa_context_disconnect.argtypes = [POINTER(pa_context)]
class pa_operation(Structure):
    pass
pa_context_drain = _libraries['libpulse.so.0'].pa_context_drain
pa_context_drain.restype = POINTER(pa_operation)
pa_context_drain.argtypes = [POINTER(pa_context), pa_context_notify_cb_t, c_void_p]
pa_context_exit_daemon = _libraries['libpulse.so.0'].pa_context_exit_daemon
pa_context_exit_daemon.restype = POINTER(pa_operation)
pa_context_exit_daemon.argtypes = [POINTER(pa_context), pa_context_success_cb_t, c_void_p]
pa_context_set_default_sink = _libraries['libpulse.so.0'].pa_context_set_default_sink
pa_context_set_default_sink.restype = POINTER(pa_operation)
pa_context_set_default_sink.argtypes = [POINTER(pa_context), STRING, pa_context_success_cb_t, c_void_p]
pa_context_set_default_source = _libraries['libpulse.so.0'].pa_context_set_default_source
pa_context_set_default_source.restype = POINTER(pa_operation)
pa_context_set_default_source.argtypes = [POINTER(pa_context), STRING, pa_context_success_cb_t, c_void_p]
pa_context_is_local = _libraries['libpulse.so.0'].pa_context_is_local
pa_context_is_local.restype = c_int
pa_context_is_local.argtypes = [POINTER(pa_context)]
pa_context_set_name = _libraries['libpulse.so.0'].pa_context_set_name
pa_context_set_name.restype = POINTER(pa_operation)
pa_context_set_name.argtypes = [POINTER(pa_context), STRING, pa_context_success_cb_t, c_void_p]
pa_context_get_server = _libraries['libpulse.so.0'].pa_context_get_server
pa_context_get_server.restype = STRING
pa_context_get_server.argtypes = [POINTER(pa_context)]
c_uint32 = c_uint32
pa_context_get_protocol_version = _libraries['libpulse.so.0'].pa_context_get_protocol_version
pa_context_get_protocol_version.restype = c_uint32
pa_context_get_protocol_version.argtypes = [POINTER(pa_context)]
pa_context_get_server_protocol_version = _libraries['libpulse.so.0'].pa_context_get_server_protocol_version
pa_context_get_server_protocol_version.restype = c_uint32
pa_context_get_server_protocol_version.argtypes = [POINTER(pa_context)]

# values for enumeration 'pa_update_mode'
pa_update_mode = c_int # enum
pa_update_mode_t = pa_update_mode
pa_context_proplist_update = _libraries['libpulse.so.0'].pa_context_proplist_update
pa_context_proplist_update.restype = POINTER(pa_operation)
pa_context_proplist_update.argtypes = [POINTER(pa_context), pa_update_mode_t, POINTER(pa_proplist), pa_context_success_cb_t, c_void_p]
pa_context_proplist_remove = _libraries['libpulse.so.0'].pa_context_proplist_remove
pa_context_proplist_remove.restype = POINTER(pa_operation)
pa_context_proplist_remove.argtypes = [POINTER(pa_context), POINTER(STRING), pa_context_success_cb_t, c_void_p]
pa_context_get_index = _libraries['libpulse.so.0'].pa_context_get_index
pa_context_get_index.restype = c_uint32
pa_context_get_index.argtypes = [POINTER(pa_context)]

# values for enumeration 'pa_stream_state'
pa_stream_state = c_int # enum
pa_stream_state_t = pa_stream_state

# values for enumeration 'pa_operation_state'
pa_operation_state = c_int # enum
pa_operation_state_t = pa_operation_state

# values for enumeration 'pa_device_type'
pa_device_type = c_int # enum
pa_device_type_t = pa_device_type

# values for enumeration 'pa_stream_direction'
pa_stream_direction = c_int # enum
pa_stream_direction_t = pa_stream_direction

# values for enumeration 'pa_stream_flags'
pa_stream_flags = c_int # enum
pa_stream_flags_t = pa_stream_flags
class pa_buffer_attr(Structure):
    _fields_ = [
        ('maxlength', c_uint32),
        ('tlength', c_uint32),
        ('prebuf', c_uint32),
        ('minreq', c_uint32),
        ('fragsize', c_uint32),
    ]

class pa_sample_spec(Structure):
    _fields_ = [
        ('format', c_int),
        ('rate', c_uint32),
        ('channels', c_uint8),
    ]

# values for enumeration 'pa_subscription_mask'
pa_subscription_mask = c_int # enum
pa_subscription_mask_t = pa_subscription_mask

# values for enumeration 'pa_subscription_event_type'
pa_subscription_event_type = c_int # enum
pa_subscription_event_type_t = pa_subscription_event_type

pa_context_subscribe_cb_t = CFUNCTYPE(None, POINTER(pa_context), pa_subscription_event_type_t, c_uint32, c_void_p)
pa_context_subscribe = _libraries['libpulse.so.0'].pa_context_subscribe
pa_context_subscribe.restype = POINTER(pa_operation)
pa_context_subscribe.argtypes = [POINTER(pa_context), pa_subscription_mask_t, pa_context_success_cb_t, c_void_p]
pa_context_set_subscribe_callback = _libraries['libpulse.so.0'].pa_context_set_subscribe_callback
pa_context_set_subscribe_callback.restype = None
pa_context_set_subscribe_callback.argtypes = [POINTER(pa_context), pa_context_subscribe_cb_t, c_void_p]




# values for enumeration 'pa_sink_flags'
pa_sink_flags = c_int # enum
pa_sink_flags_t = pa_sink_flags

# values for enumeration 'pa_sink_state'
pa_sink_state = c_int # enum
pa_sink_state_t = pa_sink_state

pa_free_cb_t = CFUNCTYPE(None, c_void_p)
pa_strerror = _libraries['libpulse.so.0'].pa_strerror
pa_strerror.restype = STRING
pa_strerror.argtypes = [c_int]

class pa_sink_info(Structure):
    pass
class pa_cvolume(Structure):
    _fields_ = [
        ('channels', c_uint8),
        ('values', pa_volume_t * 32),
    ]

class pa_channel_map(Structure):
    _fields_ = [
        ('channels', c_uint8),
        ('map', pa_channel_position_t * 32),
    ]
pa_sink_info._fields_ = [
    ('name', STRING),
    ('index', c_uint32),
    ('description', STRING),
    ('sample_spec', pa_sample_spec),
    ('channel_map', pa_channel_map),
    ('owner_module', c_uint32),
    ('volume', pa_cvolume),
    ('mute', c_int),
    ('monitor_source', c_uint32),
    ('monitor_source_name', STRING),
    ('latency', pa_usec_t),
    ('driver', STRING),
    ('flags', pa_sink_flags_t),
    ('proplist', POINTER(pa_proplist)),
    ('configured_latency', pa_usec_t),
    ('base_volume', pa_volume_t),
    ('state', pa_sink_state_t),
    ('n_volume_steps', c_uint32),
    ('card', c_uint32),
    ('n_ports', c_uint32),
    ('ports', POINTER(POINTER(pa_sink_port_info))),
    ('active_port', POINTER(pa_sink_port_info)),
    ('n_formats', c_uint8),
    ('formats', POINTER(POINTER(pa_format_info))),
]
pa_sink_info_cb_t = CFUNCTYPE(None, POINTER(pa_context), POINTER(pa_sink_info), c_int, c_void_p)
pa_context_get_sink_info_by_name = _libraries['libpulse.so.0'].pa_context_get_sink_info_by_name
pa_context_get_sink_info_by_name.restype = POINTER(pa_operation)
pa_context_get_sink_info_by_name.argtypes = [POINTER(pa_context), STRING, pa_sink_info_cb_t, c_void_p]
pa_context_get_sink_info_by_index = _libraries['libpulse.so.0'].pa_context_get_sink_info_by_index
pa_context_get_sink_info_by_index.restype = POINTER(pa_operation)
pa_context_get_sink_info_by_index.argtypes = [POINTER(pa_context), c_uint32, pa_sink_info_cb_t, c_void_p]
pa_context_get_sink_info_list = _libraries['libpulse.so.0'].pa_context_get_sink_info_list
pa_context_get_sink_info_list.restype = POINTER(pa_operation)
pa_context_get_sink_info_list.argtypes = [POINTER(pa_context), pa_sink_info_cb_t, c_void_p]
pa_context_set_sink_volume_by_index = _libraries['libpulse.so.0'].pa_context_set_sink_volume_by_index
pa_context_set_sink_volume_by_index.restype = POINTER(pa_operation)
pa_context_set_sink_volume_by_index.argtypes = [POINTER(pa_context), c_uint32, POINTER(pa_cvolume), pa_context_success_cb_t, c_void_p]
pa_context_set_sink_volume_by_name = _libraries['libpulse.so.0'].pa_context_set_sink_volume_by_name
pa_context_set_sink_volume_by_name.restype = POINTER(pa_operation)
pa_context_set_sink_volume_by_name.argtypes = [POINTER(pa_context), STRING, POINTER(pa_cvolume), pa_context_success_cb_t, c_void_p]
pa_context_set_sink_mute_by_index = _libraries['libpulse.so.0'].pa_context_set_sink_mute_by_index
pa_context_set_sink_mute_by_index.restype = POINTER(pa_operation)
pa_context_set_sink_mute_by_index.argtypes = [POINTER(pa_context), c_uint32, c_int, pa_context_success_cb_t, c_void_p]
pa_context_set_sink_mute_by_name = _libraries['libpulse.so.0'].pa_context_set_sink_mute_by_name
pa_context_set_sink_mute_by_name.restype = POINTER(pa_operation)
pa_context_set_sink_mute_by_name.argtypes = [POINTER(pa_context), STRING, c_int, pa_context_success_cb_t, c_void_p]
pa_context_suspend_sink_by_name = _libraries['libpulse.so.0'].pa_context_suspend_sink_by_name
pa_context_suspend_sink_by_name.restype = POINTER(pa_operation)
pa_context_suspend_sink_by_name.argtypes = [POINTER(pa_context), STRING, c_int, pa_context_success_cb_t, c_void_p]
pa_context_suspend_sink_by_index = _libraries['libpulse.so.0'].pa_context_suspend_sink_by_index
pa_context_suspend_sink_by_index.restype = POINTER(pa_operation)
pa_context_suspend_sink_by_index.argtypes = [POINTER(pa_context), c_uint32, c_int, pa_context_success_cb_t, c_void_p]
pa_context_set_sink_port_by_index = _libraries['libpulse.so.0'].pa_context_set_sink_port_by_index
pa_context_set_sink_port_by_index.restype = POINTER(pa_operation)
pa_context_set_sink_port_by_index.argtypes = [POINTER(pa_context), c_uint32, STRING, pa_context_success_cb_t, c_void_p]
pa_context_set_sink_port_by_name = _libraries['libpulse.so.0'].pa_context_set_sink_port_by_name
pa_context_set_sink_port_by_name.restype = POINTER(pa_operation)
pa_context_set_sink_port_by_name.argtypes = [POINTER(pa_context), STRING, STRING, pa_context_success_cb_t, c_void_p]
class pa_server_info(Structure):
    pass
pa_server_info._fields_ = [
    ('user_name', STRING),
    ('host_name', STRING),
    ('server_version', STRING),
    ('server_name', STRING),
    ('sample_spec', pa_sample_spec),
    ('default_sink_name', STRING),
    ('default_source_name', STRING),
    ('cookie', c_uint32),
    ('channel_map', pa_channel_map),
]
pa_server_info_cb_t = CFUNCTYPE(None, POINTER(pa_context), POINTER(pa_server_info), c_void_p)
pa_context_get_server_info = _libraries['libpulse.so.0'].pa_context_get_server_info
pa_context_get_server_info.restype = POINTER(pa_operation)
pa_context_get_server_info.argtypes = [POINTER(pa_context), pa_server_info_cb_t, c_void_p]
class pa_mainloop(Structure):
    pass
pa_mainloop._fields_ = [
]
pa_mainloop_new = _libraries['libpulse.so.0'].pa_mainloop_new
pa_mainloop_new.restype = POINTER(pa_mainloop)
pa_mainloop_new.argtypes = []
pa_mainloop_free = _libraries['libpulse.so.0'].pa_mainloop_free
pa_mainloop_free.restype = None
pa_mainloop_free.argtypes = [POINTER(pa_mainloop)]
pa_mainloop_prepare = _libraries['libpulse.so.0'].pa_mainloop_prepare
pa_mainloop_prepare.restype = c_int
pa_mainloop_prepare.argtypes = [POINTER(pa_mainloop), c_int]
pa_mainloop_poll = _libraries['libpulse.so.0'].pa_mainloop_poll
pa_mainloop_poll.restype = c_int
pa_mainloop_poll.argtypes = [POINTER(pa_mainloop)]
pa_mainloop_dispatch = _libraries['libpulse.so.0'].pa_mainloop_dispatch
pa_mainloop_dispatch.restype = c_int
pa_mainloop_dispatch.argtypes = [POINTER(pa_mainloop)]
pa_mainloop_get_retval = _libraries['libpulse.so.0'].pa_mainloop_get_retval
pa_mainloop_get_retval.restype = c_int
pa_mainloop_get_retval.argtypes = [POINTER(pa_mainloop)]
pa_mainloop_iterate = _libraries['libpulse.so.0'].pa_mainloop_iterate
pa_mainloop_iterate.restype = c_int
pa_mainloop_iterate.argtypes = [POINTER(pa_mainloop), c_int, POINTER(c_int)]
pa_mainloop_run = _libraries['libpulse.so.0'].pa_mainloop_run
pa_mainloop_run.restype = c_int
pa_mainloop_run.argtypes = [POINTER(pa_mainloop), POINTER(c_int)]
pa_mainloop_get_api = _libraries['libpulse.so.0'].pa_mainloop_get_api
pa_mainloop_get_api.restype = POINTER(pa_mainloop_api)
pa_mainloop_get_api.argtypes = [POINTER(pa_mainloop)]
pa_mainloop_quit = _libraries['libpulse.so.0'].pa_mainloop_quit
pa_mainloop_quit.restype = None
pa_mainloop_quit.argtypes = [POINTER(pa_mainloop), c_int]
pa_mainloop_wakeup = _libraries['libpulse.so.0'].pa_mainloop_wakeup
pa_mainloop_wakeup.restype = None
pa_mainloop_wakeup.argtypes = [POINTER(pa_mainloop)]
class pa_threaded_mainloop(Structure):
    pass
pa_threaded_mainloop._fields_ = [
]
pa_threaded_mainloop_new = _libraries['libpulse.so.0'].pa_threaded_mainloop_new
pa_threaded_mainloop_new.restype = POINTER(pa_threaded_mainloop)
pa_threaded_mainloop_new.argtypes = []
pa_threaded_mainloop_free = _libraries['libpulse.so.0'].pa_threaded_mainloop_free
pa_threaded_mainloop_free.restype = None
pa_threaded_mainloop_free.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_start = _libraries['libpulse.so.0'].pa_threaded_mainloop_start
pa_threaded_mainloop_start.restype = c_int
pa_threaded_mainloop_start.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_stop = _libraries['libpulse.so.0'].pa_threaded_mainloop_stop
pa_threaded_mainloop_stop.restype = None
pa_threaded_mainloop_stop.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_lock = _libraries['libpulse.so.0'].pa_threaded_mainloop_lock
pa_threaded_mainloop_lock.restype = None
pa_threaded_mainloop_lock.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_unlock = _libraries['libpulse.so.0'].pa_threaded_mainloop_unlock
pa_threaded_mainloop_unlock.restype = None
pa_threaded_mainloop_unlock.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_wait = _libraries['libpulse.so.0'].pa_threaded_mainloop_wait
pa_threaded_mainloop_wait.restype = None
pa_threaded_mainloop_wait.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_signal = _libraries['libpulse.so.0'].pa_threaded_mainloop_signal
pa_threaded_mainloop_signal.restype = None
pa_threaded_mainloop_signal.argtypes = [POINTER(pa_threaded_mainloop), c_int]
pa_threaded_mainloop_accept = _libraries['libpulse.so.0'].pa_threaded_mainloop_accept
pa_threaded_mainloop_accept.restype = None
pa_threaded_mainloop_accept.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_get_retval = _libraries['libpulse.so.0'].pa_threaded_mainloop_get_retval
pa_threaded_mainloop_get_retval.restype = c_int
pa_threaded_mainloop_get_retval.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_get_api = _libraries['libpulse.so.0'].pa_threaded_mainloop_get_api
pa_threaded_mainloop_get_api.restype = POINTER(pa_mainloop_api)
pa_threaded_mainloop_get_api.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_in_thread = _libraries['libpulse.so.0'].pa_threaded_mainloop_in_thread
pa_threaded_mainloop_in_thread.restype = c_int
pa_threaded_mainloop_in_thread.argtypes = [POINTER(pa_threaded_mainloop)]

pa_sw_volume_to_dB = _libraries['libpulse.so.0'].pa_sw_volume_to_dB
pa_sw_volume_to_dB.restype = c_double
pa_sw_volume_to_dB.argtypes = [pa_volume_t]

pa_operation_ref = _libraries['libpulse.so.0'].pa_operation_ref
pa_operation_ref.restype = POINTER(pa_operation)
pa_operation_ref.argtypes = [POINTER(pa_operation)]
pa_operation_unref = _libraries['libpulse.so.0'].pa_operation_unref
pa_operation_unref.restype = None
pa_operation_unref.argtypes = [POINTER(pa_operation)]
pa_operation_cancel = _libraries['libpulse.so.0'].pa_operation_cancel
pa_operation_cancel.restype = None
pa_operation_cancel.argtypes = [POINTER(pa_operation)]

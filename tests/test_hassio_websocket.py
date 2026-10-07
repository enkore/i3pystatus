import unittest


class CacheTests(unittest.TestCase):
    def test_unknown_entity_delta_is_ignored(self):
        from i3pystatus.hassio_websocket import SharedConnection
        client = SharedConnection('http://ha', 'test-only')
        client.apply_event({'c': {'sensor.unknown': {'+': {'s': 'on', 'lu': 3}}}})
        self.assertIsNone(client.entity('sensor.unknown'))

    def test_removed_entity_is_not_recreated_by_partial_delta(self):
        from i3pystatus.hassio_websocket import SharedConnection
        client = SharedConnection('http://ha', 'test-only')
        client.apply_event({'a': {'sensor.t': {'s': '21', 'a': {}, 'lc': 1}}})
        client.apply_event({'r': ['sensor.t']})
        client.apply_event({'c': {'sensor.t': {'+': {'a': {'temperature': 22}, 'lu': 2}}}})
        self.assertIsNone(client.entity('sensor.t'))

    def test_initial_compressed_snapshot(self):
        from i3pystatus.hassio_websocket import SharedConnection
        c = SharedConnection("http://ha:8123/", "secret")
        c.apply_event({"a": {"sensor.t": {"s": "21", "a": {"friendly_name": "Temp"}, "lc": 1, "lu": 2}}})
        self.assertEqual(c.entity("sensor.t"), {"entity_id": "sensor.t", "state": "21", "attributes": {"friendly_name": "Temp"}, "last_changed": "1970-01-01T00:00:01+00:00", "last_updated": "1970-01-01T00:00:02+00:00"})

    def test_delta_merge_removals_and_copy_isolation(self):
        from i3pystatus.hassio_websocket import SharedConnection
        c = SharedConnection("http://ha", "secret")
        c.apply_event({"a": {"sensor.t": {"s": "21", "a": {"keep": 1, "remove": 2}, "lc": 1}}})
        c.apply_event({"c": {"sensor.t": {"+": {"s": "22", "a": {"new": 3}, "lu": 4}, "-": {"a": ["remove"]}}}})
        state = c.entity("sensor.t")
        self.assertEqual(state["state"], "22")
        self.assertEqual(state["attributes"], {"keep": 1, "new": 3})
        state["attributes"]["keep"] = 99
        self.assertEqual(c.entity("sensor.t")["attributes"]["keep"], 1)
        c.apply_event({"r": ["sensor.t"]})
        self.assertIsNone(c.entity("sensor.t"))

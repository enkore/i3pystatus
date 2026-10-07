import unittest


class TimestampTests(unittest.TestCase):
    def test_last_changed_takes_precedence_over_explicit_last_updated(self):
        from i3pystatus.hassio.websocket import SharedConnection
        client = SharedConnection('http://ha', 'test-only')
        client.apply_event({'a': {'sensor.t': {'s': '21', 'a': {}, 'lc': 1, 'lu': 2}}})
        client.apply_event({'c': {'sensor.t': {'+': {'s': '22', 'lc': 3, 'lu': 4}}}})
        entity = client.entity('sensor.t')
        self.assertEqual(entity['last_updated'], entity['last_changed'])

    def test_last_updated_only_preserves_last_changed(self):
        from i3pystatus.hassio.websocket import SharedConnection
        client = SharedConnection('http://ha', 'test-only')
        client.apply_event({'a': {'sensor.t': {'s': '21', 'a': {}, 'lc': 1}}})
        client.apply_event({'c': {'sensor.t': {'+': {'lu': 4}}}})
        entity = client.entity('sensor.t')
        self.assertEqual(entity['last_changed'], '1970-01-01T00:00:01+00:00')
        self.assertEqual(entity['last_updated'], '1970-01-01T00:00:04+00:00')

    def test_last_changed_delta_also_advances_last_updated(self):
        from i3pystatus.hassio.websocket import SharedConnection
        client = SharedConnection('http://ha', 'test-only')
        client.apply_event({'a': {'sensor.t': {'s': '21', 'a': {}, 'lc': 1, 'lu': 2}}})
        client.apply_event({'c': {'sensor.t': {'+': {'s': '22', 'lc': 3}}}})
        entity = client.entity('sensor.t')
        self.assertEqual(entity['last_updated'], entity['last_changed'])
        self.assertEqual(entity['last_updated'], '1970-01-01T00:00:03+00:00')

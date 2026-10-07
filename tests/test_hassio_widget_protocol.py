import unittest
from unittest.mock import Mock, patch

from i3pystatus.hassio import Hassio
from i3pystatus.hassio_websocket import SharedConnection


class WidgetTests(unittest.TestCase):
    def test_same_module_renders_websocket_without_polling(self):
        client = SharedConnection('http://ha', 'test-only')
        client.status = 'ready'
        client.apply_event({'a': {'climate.garage': {'s': 'heat', 'a': {'current_temperature': 72.5}, 'lc': 1}}})
        client.add = Mock()
        handler = Mock()
        widget = Hassio(hassio_url='http://ha', hassio_token='test-only',
                        entity_id='climate.garage', protocol='websocket',
                        format='Garage temp: {current_temperature}')
        with patch('i3pystatus.hassio_websocket.get_connection', return_value=client), patch('i3pystatus.hassio.get', side_effect=AssertionError('REST poll')):
            widget.registered(handler)
            callback = client.add.call_args[0][1]
            client.apply_event({'c': {'climate.garage': {'+': {'a': {'current_temperature': 73}}}}})
            callback()
            self.assertEqual(widget.output['full_text'], 'Garage temp: 73')
            handler.io.async_refresh.assert_called()
            client.status = 'disconnected'
            callback()
            self.assertIn('stale', widget.output['full_text'])
            self.assertIn('73', widget.output['full_text'])
            client.status = 'ready'
            callback()
            self.assertEqual(widget.output['full_text'], 'Garage temp: 73')

    def test_missing_attribute_is_visible_and_later_recovers(self):
        client = SharedConnection('http://ha', 'test-only')
        client.status = 'ready'
        client.add = Mock()
        client.apply_event({'a': {'climate.garage': {'s': 'heat', 'a': {}, 'lc': 1}}})
        widget = Hassio(hassio_url='http://ha', hassio_token='test-only', entity_id='climate.garage',
                        protocol='websocket', format='Garage temp: {current_temperature}')
        with patch('i3pystatus.hassio_websocket.get_connection', return_value=client):
            widget.registered(Mock())
            self.assertIn('current_temperature', widget.output['full_text'])
            client.apply_event({'c': {'climate.garage': {'+': {'a': {'current_temperature': 73}}}}})
            client.add.call_args[0][1]()
            self.assertEqual(widget.output['full_text'], 'Garage temp: 73')

    def test_rest_is_default_and_protocol_is_validated(self):
        kwargs = dict(hassio_url='http://ha', hassio_token='test-only', entity_id='sensor.t')
        self.assertEqual(Hassio(**kwargs).protocol, 'rest')
        with self.assertRaises(ValueError):
            Hassio(protocol='typo', **kwargs)

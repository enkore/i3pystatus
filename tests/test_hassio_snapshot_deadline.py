import asyncio
import itertools
import json
import unittest
from unittest.mock import Mock, patch

from i3pystatus.hassio_websocket import SharedConnection


class SnapshotDeadlineTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(asyncio, 'run'), 'Requires Python 3.7+')
    def test_unrelated_frames_do_not_suppress_snapshot_deadline(self):
        class Socket:
            def __init__(self):
                self.received = 0

            async def recv(self):
                await asyncio.sleep(0)
                self.received += 1
                if self.received == 1:
                    return json.dumps({'type': 'auth_required'})
                if self.received == 2:
                    return json.dumps({'type': 'auth_ok'})
                if self.received > 20:
                    raise AssertionError('Continuous frames suppressed the snapshot deadline')
                return json.dumps({'id': 999, 'type': 'result', 'success': True})

            async def send(self, message):
                pass

        clock = Mock()
        clock.time.side_effect = itertools.chain([0], itertools.repeat(20))
        client = SharedConnection('http://test-only', 'test-only')
        with patch('i3pystatus.hassio_websocket.asyncio.get_event_loop', return_value=clock):
            with self.assertRaisesRegex(TimeoutError, 'Initial entity snapshot timed out'):
                asyncio.run(client._session(Socket()))

import asyncio
import json
import unittest

try:
    try:
        from websockets.asyncio.server import serve
    except ImportError:
        from websockets.server import serve
except ImportError:
    serve = None


@unittest.skipIf(serve is None, 'Requires optional websockets dependency')
class TransportTests(unittest.TestCase):
    def test_shared_filtered_subscription_and_late_widget(self):
        from i3pystatus.hassio_websocket import get_connection

        async def scenario():
            sockets, subscriptions, notifications = [], [], []

            async def handler(ws, _path=None):
                sockets.append(ws)
                await ws.send(json.dumps({'type': 'auth_required'}))
                auth = json.loads(await ws.recv())
                self.assertEqual(auth['access_token'], 'test-only')
                await ws.send(json.dumps({'type': 'auth_ok'}))
                async for raw in ws:
                    msg = json.loads(raw)
                    await ws.send(json.dumps({'id': msg['id'], 'type': 'result', 'success': True}))
                    if msg['type'] == 'subscribe_entities':
                        subscriptions.append(msg)
                        states = {e: {'s': '21', 'a': {'temperature': 21}, 'lc': 1} for e in msg['entity_ids']}
                        await ws.send(json.dumps({'id': msg['id'], 'type': 'event', 'event': {'a': states}}))
                        await ws.send(json.dumps({'id': msg['id'], 'type': 'event', 'event': {'c': {'sensor.a': {'+': {'a': {'temperature': 22}, 'lu': 2}}}}}))

            async with serve(handler, '127.0.0.1', 0) as server:
                port = server.sockets[0].getsockname()[1]
                url = 'http://localhost:' + str(port)
                client = get_connection(url, 'test-only')
                self.assertIs(client, get_connection(url + '/', 'test-only'))
                self.assertIsNot(client, get_connection(url, 'other-test'))
                client.add('sensor.a', lambda: notifications.append(client.status))
                client.add('sensor.b', lambda: notifications.append(client.status))
                try:
                    for _ in range(200):
                        a = client.entity('sensor.a')
                        if client.entity('sensor.b') and a['attributes'].get('temperature') == 22:
                            break
                        await asyncio.sleep(.02)
                    self.assertEqual(client.status, 'ready')
                    self.assertEqual(len(sockets), 1)
                    self.assertEqual(len(subscriptions), 1)
                    self.assertEqual(subscriptions[0]['entity_ids'], ['sensor.a', 'sensor.b'])
                    self.assertEqual(a['attributes']['temperature'], 22)
                    self.assertIn('ready', notifications)
                    client.add('sensor.c', lambda: None)
                    for _ in range(200):
                        if client.entity('sensor.c'):
                            break
                        await asyncio.sleep(.02)
                    self.assertIsNotNone(client.entity('sensor.c'))
                    self.assertEqual(len(sockets), 1)
                    self.assertEqual(len(subscriptions), 2)
                    self.assertEqual(subscriptions[-1]['entity_ids'], ['sensor.a', 'sensor.b', 'sensor.c'])
                finally:
                    client.stop()
                    await asyncio.sleep(.4)
        asyncio.run(scenario())

    def test_reconnect_refreshes_snapshot_and_resets_backoff(self):
        from i3pystatus.hassio_websocket import SharedConnection

        async def scenario():
            times, statuses = [], []

            async def handler(ws, _path=None):
                times.append(asyncio.get_running_loop().time())
                count = len(times)
                await ws.send(json.dumps({'type': 'auth_required'}))
                await ws.recv()
                await ws.send(json.dumps({'type': 'auth_ok'}))
                sub = json.loads(await ws.recv())
                states = {'sensor.a': {'s': str(count), 'a': {}, 'lc': count}}
                if count == 1:
                    states['sensor.removed'] = {'s': 'old', 'a': {}, 'lc': 1}
                await ws.send(json.dumps({'id': sub['id'], 'type': 'event', 'event': {'a': states}}))
                if count < 4:
                    await asyncio.sleep(.05)
                    await ws.close()
                else:
                    await ws.wait_closed()
            async with serve(handler, '127.0.0.1', 0) as server:
                client = SharedConnection('http://localhost:' + str(server.sockets[0].getsockname()[1]), 'test-only')
                client.retry_delay = .1
                client.add('sensor.a', lambda: statuses.append(client.status))
                client.add('sensor.removed', lambda: None)
                try:
                    for _ in range(250):
                        state = client.entity('sensor.a')
                        if state and state['state'] == '4' and client.status == 'ready':
                            break
                        await asyncio.sleep(.02)
                    self.assertEqual(state['state'], '4')
                    self.assertIsNone(client.entity('sensor.removed'))
                    self.assertIn('disconnected', statuses)
                    self.assertLess(times[3] - times[2], .35)
                finally:
                    client.stop()
                    await asyncio.sleep(.4)
        asyncio.run(scenario())

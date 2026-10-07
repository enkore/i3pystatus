"""Internal shared Home Assistant subscription used by the hassio module."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
import threading
from urllib.parse import urlsplit, urlunsplit


_connections = {}
_connections_lock = threading.Lock()
_LOG = logging.getLogger(__name__)


def get_connection(url, token):
    key = (url.rstrip('/'), token)
    with _connections_lock:
        if key not in _connections:
            _connections[key] = SharedConnection(*key)
        return _connections[key]


class SubscriptionError(Exception):
    """Authentication or subscription requires a configuration change."""


class SharedConnection:
    retry_delay = 1

    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.token = token
        self.states = {}
        self.lock = threading.RLock()
        self.status = 'connecting'
        self._callbacks = {}
        self._generation = 0
        self._thread = None
        self._stopped = threading.Event()

    def add(self, entity_id, callback):
        # Optional dependency: REST users need not install websockets.
        import websockets  # noqa: F401
        with self.lock:
            self._callbacks.setdefault(entity_id, []).append(callback)
            self._generation += 1
            if self._thread is None:
                self._thread = threading.Thread(target=self._worker, name='hassio-websocket', daemon=True)
                self._thread.start()

    def refresh(self):
        """Request a fresh snapshot on the existing connection."""
        with self.lock:
            self._generation += 1

    def stop(self):
        self._stopped.set()

    def _notify(self, entity_ids=None):
        with self.lock:
            callbacks = [cb for eid, items in self._callbacks.items()
                         if entity_ids is None or eid in entity_ids for cb in items]
        for cb in callbacks:
            try:
                cb()
            except Exception:
                # A bad widget must not break the other subscribers.
                _LOG.error('Home Assistant widget callback failed', exc_info=True)

    def _set_status(self, status):
        with self.lock:
            changed = self.status != status
            self.status = status
        if changed:
            self._notify()

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._listen())
        finally:
            loop.close()

    async def _listen(self):
        import websockets
        parts = urlsplit(self.url)
        scheme = {'http': 'ws', 'https': 'wss', 'ws': 'ws', 'wss': 'wss'}.get(parts.scheme)
        if scheme is None:
            self._set_status('configuration error')
            return
        url = urlunsplit((scheme, parts.netloc, parts.path.rstrip('/') + '/api/websocket', '', ''))
        delay = self.retry_delay
        # Batch widgets registered together; later additions resubscribe in place.
        await asyncio.sleep(.05)
        while not self._stopped.is_set():
            try:
                async with websockets.connect(url, open_timeout=10, close_timeout=2,
                                              ping_interval=20, ping_timeout=20,
                                              max_size=4 * 1024 * 1024) as ws:
                    await self._session(ws)
            except SubscriptionError as exc:
                self._set_status(str(exc))
                return
            except Exception as exc:
                if self.status == 'ready':
                    delay = self.retry_delay
                self._set_status('disconnected')
                # Never log authentication messages or exception text containing credentials.
                _LOG.warning('Home Assistant WebSocket disconnected (%s); reconnecting', type(exc).__name__)
            if self._stopped.is_set():
                break
            if self.status == 'ready':
                delay = self.retry_delay
            # Event.wait would block this thread's asyncio loop; small sleeps allow stop.
            remaining = delay
            while remaining > 0 and not self._stopped.is_set():
                step = min(.25, remaining)
                await asyncio.sleep(step)
                remaining -= step
            delay = min(delay * 2, 60)
        self._set_status('disconnected')

    async def _session(self, ws):
        hello = json.loads(await asyncio.wait_for(ws.recv(), 10))
        if hello.get('type') != 'auth_required':
            raise SubscriptionError('authentication error')
        await ws.send(json.dumps({'type': 'auth', 'access_token': self.token}))
        auth = json.loads(await asyncio.wait_for(ws.recv(), 10))
        if auth.get('type') != 'auth_ok':
            raise SubscriptionError('authentication error')
        generation, subscription, counter = -1, None, 0
        initial = True
        while not self._stopped.is_set():
            with self.lock:
                current = self._generation
                entity_ids = sorted(self._callbacks)
            if current != generation:
                if subscription is not None:
                    counter += 1
                    await ws.send(json.dumps({'id': counter, 'type': 'unsubscribe_events', 'subscription': subscription}))
                counter += 1
                subscription = counter
                await ws.send(json.dumps({'id': subscription, 'type': 'subscribe_entities', 'entity_ids': entity_ids}))
                generation, initial = current, True
                self._set_status('connecting')
                deadline = asyncio.get_event_loop().time() + 10
            if initial and asyncio.get_event_loop().time() > deadline:
                raise TimeoutError('Initial entity snapshot timed out')
            try:
                raw = await asyncio.wait_for(ws.recv(), .25)
            except asyncio.TimeoutError:
                if initial and asyncio.get_event_loop().time() > deadline:
                    raise TimeoutError('Initial entity snapshot timed out')
                continue
            msg = json.loads(raw)
            if msg.get('id') != subscription:
                continue
            if msg.get('type') == 'result' and not msg.get('success'):
                raise SubscriptionError('subscription error')
            if msg.get('type') == 'event':
                event = msg['event']
                if initial:
                    with self.lock:
                        self.states.clear()
                    initial = False
                self.apply_event(event)
                if self.status != 'ready':
                    self._set_status('ready')
                else:
                    changed = set(event.get('a', {})) | set(event.get('c', {})) | set(event.get('r', []))
                    self._notify(changed)

    def apply_event(self, event):
        with self.lock:
            self.states.update(deepcopy(event.get('a', {})))
            for entity_id, delta in event.get('c', {}).items():
                state = self.states.get(entity_id)
                if state is None:
                    continue
                added = deepcopy(delta.get('+', {}))
                state.setdefault('a', {}).update(added.pop('a', {}))
                state.update(added)
                if 'lc' in added:
                    state['lu'] = added['lc']
                for key in delta.get('-', {}).get('a', []):
                    state['a'].pop(key, None)
            for entity_id in event.get('r', []):
                self.states.pop(entity_id, None)

    def entity(self, entity_id):
        with self.lock:
            state = deepcopy(self.states.get(entity_id))
        if state is None:
            return None

        def timestamp(value):
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value, timezone.utc).isoformat()
            return value

        return {'entity_id': entity_id, 'state': state.get('s'),
                'attributes': state.get('a', {}),
                'last_changed': timestamp(state.get('lc')),
                'last_updated': timestamp(state.get('lu', state.get('lc')))}

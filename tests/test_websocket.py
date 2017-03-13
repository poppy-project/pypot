import sys
import json
import time
import unittest
import websocket

from pypot.creatures import PoppyErgoJr
from utils import get_open_port


if sys.version_info[0] < 3:
    import socket
    ConnectionError = socket.error


class TestWebsocketsCommunication(unittest.TestCase):
    """docstring for TestWebsocketsCommunication"""
    def setUp(self):
        port = get_open_port()
        self.jr = PoppyErgoJr(simulator='poppy-simu', use_ws=True, ws_port=port)

        self.ws_url = 'ws://127.0.0.1:{}'.format(port)

        while True:
            try:
                self.ws = websocket.WebSocket()
                self.ws.connect(self.ws_url)
                break
            except ConnectionError:
                time.sleep(1.0)

    def tearDown(self):
        self.ws.close()

    def test_connected(self):
        self.assertTrue(self.ws.connected)

    def test_recv_state(self):
        state = json.loads(self.ws.recv())
        self.assertSetEqual(set(state.keys()),
                            {m.name for m in self.jr.motors})

    def test_led(self):
        obj = {
            'm1': {
                'led': 'red'
            }
        }
        self.ws.send(json.dumps(obj))


if __name__ == '__main__':
    unittest.main()

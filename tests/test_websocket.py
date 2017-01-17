import unittest
import websocket
import json

from pypot.creatures import PoppyErgoJr
from utils import get_open_port

class TestWebsocketsCommunication(unittest.TestCase):
    """docstring for TestWebsocketsCommunication"""
    def setUp(self):
        port = get_open_port()
        self.jr = PoppyErgoJr(simulator='poppy-simu', use_ws=True, ws_port=port)
        self.ws_url = 'ws://127.0.0.1:{}'.format(port)
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url)

    def test_led(self):
        obj = {
            'm1': {
                'led': 'red'
            }
        }
        self.ws.send(json.dumps(obj))


if __name__ == '__main__':
    unittest.main()

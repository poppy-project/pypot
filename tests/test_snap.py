import unittest
import requests
import random
import time

from pypot.creatures import PoppyErgoJr
from pypot.dynamixel.conversion import XL320LEDColors

from utils import get_open_port


class TestSnap(unittest.TestCase):
    def setUp(self):
        port = get_open_port()

        self.jr = PoppyErgoJr(simulator='poppy-simu', use_snap=True, snap_port=port)
        self.base_url = 'http://127.0.0.1:{}'.format(port)

        # Make sure the Snap API is running before actually testing.
        while True:
            try:
                self.get('/')
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)

    def get(self, url):
        url = '{}{}'.format(self.base_url, url)
        return requests.get(url)

    def test_led(self):
        c = random.choice(list(XL320LEDColors))
        m = random.choice(self.jr.motors)

        r = self.get('/motor/{}/set/led/{}'.format(m.name, c.name))
        self.assertEqual(r.status_code, 200)

        r = self.get('/motor/{}/get/led'.format(m.name))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, c.name)


if __name__ == '__main__':
    unittest.main()

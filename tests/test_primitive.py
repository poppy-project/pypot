import unittest
import random
import time

from poppy.creatures import PoppyErgoJr


class TestPrimTeardown(unittest.TestCase):
    def setUp(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu')

    def test_teardown(self):
        self.jr.dance.start()
        time.sleep(random.random() * 5)
        self.jr.dance.stop()

        self.assertEqual({m.led for m in self.jr.motors}, {'off'})
        self.assertEqual({m.led for m in self.jr.dance.robot.motors}, {'off'})

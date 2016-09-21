import time
import unittest

from pypot.creatures import PoppyErgoJr
from pypot.primitive import LoopPrimitive

from utils import get_open_port


class EmptyPrim(LoopPrimitive):
    def setup(self):
        pass

    def update(self):
        pass

    def teardown(self):
        pass


class TestDummy(unittest.TestCase):
    def setUp(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu',
                              http_api_port=get_open_port())

    def test_dummy_controller(self):
        for m in self.jr.motors:
            m.moving_speed = 10000
            m.goal_position = 25

        # Make sure it was synced
        self.jr._controllers[0]._updated.clear()
        self.jr._controllers[0]._updated.wait()

        for m in self.jr.motors:
            self.assertEqual(m.goal_position, m.present_position)

    def test_empty_primitive(self):
        p = EmptyPrim(self.jr, 50.0)
        p.start()
        p.stop()

    def tearDown(self):
        self.jr.close()


if __name__ == '__main__':
    unittest.main()

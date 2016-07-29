import time
import unittest

from pypot.creatures import PoppyErgoJr

from utils import get_open_port


class TestIK(unittest.TestCase):
    def setUp(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu',
                              rest_api_port=get_open_port())

    def test_dummy_controller(self):
        for m in self.jr.motors:
            m.goal_position = 25

        # Make sure it was synced
        self.jr._controllers[0]._updated.clear()
        self.jr._controllers[0]._updated.wait()

        for m in self.jr.motors:
            self.assertEqual(m.goal_position, m.present_position)


if __name__ == '__main__':
    unittest.main()

import time
import unittest

from poppy.creatures import PoppyErgoJr


class TestIK(unittest.TestCase):
    def setUp(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu')

    def test_dummy_controller(self):
        for m in self.jr.motors:
            m.goal_position = 25

        # Make sure it was synced
        self.jr._controllers[0]._updated.clear()
        self.jr._controllers[0]._updated.wait()

        for m in self.jr.motors:
            self.assertEqual(m.goal_position, m.present_position)

    def tearDown(self):
        self.jr.close()


if __name__ == '__main__':
    unittest.main()

import unittest

from pypot.robot.controller import MotorsController


class ShittyController(MotorsController):
    def setup(self):
        raise Exception("Sorry I didn't do it on purpose...")


class TestPrimLifeCycle(unittest.TestCase):
    def test_crashed_at_setup(self):
        sc = ShittyController(None, [], 50.)
        with self.assertRaises(RuntimeError):
            sc.start()


if __name__ == '__main__':
    unittest.main()

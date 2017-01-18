import unittest

from pypot.creatures import PoppyErgoJr


class TestIK(unittest.TestCase):
    def test_lowerlimit_correctly_setup(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu')
        self.jr.close()
        # TODO: We should also make a unit test with a real/vrep robot.


if __name__ == '__main__':
    unittest.main()

import unittest

from poppy.creatures import PoppyErgoJr


class TestIK(unittest.TestCase):
    def test_lowerlimit_correctly_setup(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu')

        # TODO: We should also make a unit test with a real/vrep robot.

if __name__ == '__main__':
    unittest.main()

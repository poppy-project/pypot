import unittest

from pypot.creatures import PoppyErgoJr

from utils import get_open_port


class TestIK(unittest.TestCase):
    def test_lowerlimit_correctly_setup(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu',
                              http_api_port=get_open_port())

        # TODO: We should also make a unit test with a real/vrep robot.

if __name__ == '__main__':
    unittest.main()

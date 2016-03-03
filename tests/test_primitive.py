import unittest
import random
import time

from poppy.creatures import PoppyErgoJr
from pypot.primitive import LoopPrimitive


class TestPrimLifeCycle(unittest.TestCase):
    def setUp(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu')

    def test_teardown(self):
        self.jr.dance.start()
        time.sleep(random.random() * 5)
        self.jr.dance.stop()

        self.assertEqual({m.led for m in self.jr.motors}, {'off'})
        self.assertEqual({m.led for m in self.jr.dance.robot.motors}, {'off'})

    def test_set_once(self):
        class Switcher(LoopPrimitive):
            def setup(self):
                self.current_state = False
                self.old_state = self.current_state

            def update(self):
                if self.current_state != self.old_state:
                    for m in self.robot.motors:
                        self.affect_once(m, 'led',
                                         'red' if self.current_state else 'off')

                    self.old_state = self.current_state

        p = Switcher(self.jr, 10)
        p.start()

        for m in self.jr.motors:
            m.led = 'off'

        self.jr.m3.led = 'pink'

        self.assertEqual([m.led for m in self.jr.motors],
                         ['off', 'off', 'pink', 'off', 'off', 'off'])

        p.current_state = not p.current_state
        time.sleep(.3)

        self.assertEqual([m.led for m in self.jr.motors],
                         ['red', 'red', 'red', 'red', 'red', 'red'])

        self.jr.m3.led = 'blue'
        self.assertEqual([m.led for m in self.jr.motors],
                         ['red', 'red', 'blue', 'red', 'red', 'red'])

        p.stop()


if __name__ == '__main__':
    unittest.main()

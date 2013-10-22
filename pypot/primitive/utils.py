import numpy

import pypot.robot
import pypot.primitive


class Sinus(pypot.primitive.LoopPrimitive):
    """ Apply a sinus on the motor specified as argument. """
    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):

        pypot.primitive.LoopPrimitive.__init__(self, robot, refresh_freq,
                                               amp, freq, offset, phase)

        self.motor_list = [self._get_mockup_motor(m) for m in motor_list]


    def update(self, amp, freq, phase, offset):
        """ Compute the sin(t) where t is the elapsed time since the primitive has been started. """
        pos = amp * numpy.sin(freq * 2.0 * numpy.pi * self.elapsed_time + \
                              phase * numpy.pi / 180.0) + offset

        for m in self.motor_list:
            m.goal_position = pos


class Cosinus(Sinus):
    """ Apply a cosinus on the motor specified as argument. """
    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):

        Sinus.__init__(self, robot, refresh_freq,
                       motor_list,
                       amp, freq, offset, phase=(numpy.pi / 2 + phase))


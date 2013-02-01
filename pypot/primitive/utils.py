import numpy
import itertools

import pypot.robot
import pypot.primitive


class Sinus(pypot.primitive.LoopPrimitive):
    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):
        
        pypot.primitive.LoopPrimitive.__init__(self, robot, refresh_freq)
        
        self.motor_list = map(self._get_mockup_motor, motor_list)
        self.amp = amp
        self.freq = freq
        self.offset = offset
        self.phase = phase
    
    
    def update(self, amp, freq, phs, offset):
        pos = self.amp * numpy.sin(self.freq * 2.0 * numpy.pi * self.elapsed_time + \
                                   self.phase * numpy.pi / 180.0) + self.offset

        for m in self.motor_list:
            m.goal_position = pos


class Cosinus(Sinus):
    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):
        
        Sinus.__init__(self, robot, refresh_freq,
                       motor_list,
                       amplitude, frequence, offset, phase=numpy.pi/2+phase)


import numpy

import pypot.primitive

class Sinus(pypot.primitive.LoopPrimitive):
    def __init__(self, robot, refresh_freq, period, amp, phs):
        pypot.primitive.LoopPrimitive.__init__(self, robot, refresh_freq)
        
        step = (2 * numpy.pi) / (period * refresh_freq)
        self.values = numpy.sin(numpy.arange(0, 2 * numpy.pi, step)) * amp
        self.i = int(((phs / period) * len(self.values)) % len(self.values))
    
    def update(self):
        for m in self.robot.motors:
            m.goal_position = self.values[self.i]
        
        self.i += 1
        if self.i >= len(self.values):
            self.i = 0
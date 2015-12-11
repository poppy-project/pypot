import numpy

from copy import deepcopy
from collections import defaultdict

from .primitive import Primitive, LoopPrimitive


class Sinus(LoopPrimitive):
    """ Apply a sinus on the motor specified as argument. Parameters (amp, offset and phase) should be specified in degree. """
    properties = LoopPrimitive.properties + ['frequency', 'amplitude', 'offset', 'phase']

    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):

        LoopPrimitive.__init__(self, robot, refresh_freq)

        self._freq = freq
        self._amp = amp
        self._offset = offset
        self._phase = phase

        self.motor_list = [self.get_mockup_motor(m) for m in motor_list]

    def update(self):
        """ Compute the sin(t) where t is the elapsed time since the primitive has been started. """
        pos = self._amp * numpy.sin(self._freq * 2.0 * numpy.pi * self.elapsed_time +
                                    self._phase * numpy.pi / 180.0) + self._offset

        for m in self.motor_list:
            m.goal_position = pos

    @property
    def frequency(self):
        return self._freq

    @frequency.setter
    def frequency(self, new_freq):
        self._freq = new_freq

    @property
    def amplitude(self):
        return self._amp

    @amplitude.setter
    def amplitude(self, new_amp):
        self._amp = new_amp

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, new_offset):
        self._offset = new_offset

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, new_phase):
        self._phase = new_phase


class Cosinus(Sinus):
    """ Apply a cosinus on the motor specified as argument. Parameters (amp, offset and phase) should be specified in degree. """

    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):

        Sinus.__init__(self, robot, refresh_freq,
                       motor_list,
                       amp, freq, offset, phase=(numpy.pi / 2 + phase))


class PositionWatcher(LoopPrimitive):
    def __init__(self, robot, refresh_freq, watched_motors):
        LoopPrimitive.__init__(self, robot, refresh_freq)

        self._pos = defaultdict(list)
        self.watched_motors = watched_motors
        self._duration = 0.

    @property
    def record_positions(self):
        return deepcopy(self._pos)

    def setup(self):
        self._pos.clear()

    def update(self):
        for m in self.watched_motors:
            self._pos[m.name].append(m.present_position)

        self._duration = self.elapsed_time

    def plot(self, ax):
        for m, pos in self._pos.items():
            t = numpy.linspace(0, self._duration, len(pos))
            ax.plot(t, pos)
        ax.set_ylabel('position (in deg)')
        ax.set_xlabel('time (in s)')
        ax.legend(self._pos.keys(), loc='best')


class SimplePosture(Primitive):
    def __init__(self, robot, duration):
        Primitive.__init__(self, robot)

        self.duration = duration

    def setup(self):
        self._speeds = {m: m.moving_speed for m in self.robot.motors}

        if hasattr(self, 'leds'):
            for m, c in self.leds.items():
                m.led = c

    def run(self):
        if not hasattr(self, 'target_position'):
            raise NotImplementedError('You have to define "target_position" first!')

        for m in self.robot.motors:
            m.compliant = False

        self.robot.goto_position(self.target_position, self.duration, wait=True)

    def teardown(self):
        for m, s in self._speeds.items():
            m.moving_speed = s

        if hasattr(self, 'leds'):
            for m, c in self.leds.items():
                m.led = 'off'

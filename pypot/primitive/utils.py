import numpy

from .primitive import LoopPrimitive


class Sinus(LoopPrimitive):

    """ Apply a sinus on the motor specified as argument. Parameters (amp, offset and phase) should be specified in degree
    """

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

    """ Apply a cosinus on the motor specified as argument. Parameters (amp, offset and phase) should be specified in degree
    """

    def __init__(self, robot, refresh_freq,
                 motor_list,
                 amp=1, freq=0.5, offset=0, phase=0):

        Sinus.__init__(self, robot, refresh_freq,
                       motor_list,
                       amp, freq, offset, phase=(numpy.pi / 2 + phase))

try:
    from scipy import signal

    class Square(Sinus):
        """ Apply a square signal. Param (amp, freq, offset, phase, duty cycle). """

        def __init__(self, robot, refresh_freq,
                     motor_list,
                     amp=1, freq=1.0, offset=0, phase=0, duty=0.5):

            Sinus.__init__(self, robot, refresh_freq,
                           motor_list,
                           amp, freq, offset, phase)

            self._duty = duty

        def update(self):

            pos = self._amp * signal.square(self._freq * 2.0 * numpy.pi *
                                            self.elapsed_time + self._phase * numpy.pi / 180.0, self._duty) + self._offset

            for m in self.motor_list:
                m.goal_position = pos
            print pos

        @property
        def duty(self):
            return self._duty

        @duty.setter
        def duty(self, new_duty):
            self._duty = new_duty

except ImportError:
    pass

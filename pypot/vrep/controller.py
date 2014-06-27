import time

from numpy import rad2deg, deg2rad

from .io import VrepIO
from ..robot.controller import AbstractController


class VrepController(AbstractController):
    """

    """
    def __init__(self, vrep_host, vrep_port, motors, sync_freq=50.):
        """ """
        vrep_io = VrepIO(vrep_host, vrep_port)
        AbstractController.__init__(self, vrep_io, motors, sync_freq)

    def sync_values(self):
        self._init_vrep_streaming()

        while self.running():
            for m in self.motors:
                # Read values from V-REP and set them to the Motor
                p = round(rad2deg(self.io.get_motor_position(m.name)), 1)
                m._values['present_position'] = p

                # Send new values from Motor to V-REP
                p = deg2rad(round(m._values['goal_position'], 1))
                self.io.set_motor_position(m.name, p)

            time.sleep(self._sync_period)

    def _init_vrep_streaming(self):
        pos = [self.io.get_motor_position(motor_name=m.name) for m in self.motors]

        for m, p in zip(self.motors, pos):
            # self.io.set_motor_position(m.name, p)
            self.io.set_motor_position(m.name, 0.)

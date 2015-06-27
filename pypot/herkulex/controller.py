import time
import itertools

from pypot.robot.controller import MotorsController


class HkxController(MotorsController):
    """ Synchronizes the reading/writing of :class:`~pypot.herkulex.motor.HkxMotor` with the real motors.

        This class handles synchronization loops that automatically read/write values from the "software" :class:`~pypot.herkulex.motor.HkxMotor` with their "hardware" equivalent. Those loops shared a same :class:`~pypot.herkulex.io.HkxIO` connection to avoid collision in the bus. Each loop run within its own thread as its own frequency.

        .. warning:: As all the loop attached to a controller shared the same bus, you should make sure that they can run without slowing down the other ones.

        """
    def __init__(self, io, motors, controllers):
        MotorsController.__init__(self, io, motors, 1.)
        self.controllers = controllers

    def setup(self):
        """ Starts all the synchronization loops. """
        [c.start() for c in self.controllers]
        [c.wait_to_start() for c in self.controllers]

    def update(self):
        pass

    def teardown(self):
        """ Stops the synchronization loops. """
        [c.stop() for c in self.controllers]


class BaseHkxController(HkxController):
    """ Implements a basic controller that synchronizes the most frequently used values.

    More precisely, this controller:
        * reads the present position, speed, load at 50Hz
        * reads the angle limits, present voltage and temperature at 1Hz

    """
    def __init__(self, io, motors):
        factory = _HkxRegisterController

        controllers = [_PosSpeedLoadHkxController(io, motors, 50),
                       AngleLimitRegisterController(io, motors,
                                                    1, 'get', 'angle_limit'),
                       factory(io, motors, 1, 'get', 'present_voltage_temperature')]

        models = set(m.model for m in motors)

        HkxController.__init__(self, io, motors, controllers)


class _HkxController(MotorsController):
    def __init__(self, io, motors, sync_freq=50.):
        MotorsController.__init__(self, io, motors, sync_freq)

        self.ids = [m.id for m in self.working_motors]

    @property
    def working_motors(self):
        return [m for m in self.motors if not m._broken]


class _HkxRegisterController(_HkxController):
    def __init__(self, io, motors, sync_freq,
                 mode, regname, varname=None):
        _HkxController.__init__(self, io, motors, sync_freq)

        self.mode = mode
        self.regname = regname
        self.varname = regname if varname is None else varname

    def setup(self):
        if self.mode == 'set':
            MAX_TRIALS = 25
            for _ in range(MAX_TRIALS):
                if self.get_register():
                    break
                time.sleep(0.1)
            else:
                raise IOError('Cannot initialize syncloop for "{}"'.format(
                              self.regname))

    def update(self):
        self.get_register() if self.mode == 'get' else self.set_register()

    def get_register(self):
        """ Gets the value from the specified register and sets it to the :class:`~pypot.herkulex.motor.HkxMotor`. """
        motors = [m for m in self.working_motors if hasattr(m, self.varname)]
        if not motors:
            return False
        ids = [m.id for m in motors]

        values = getattr(self.io, 'get_{}'.format(self.regname))(ids)
        if not values:
            return False

        for m, val in zip(motors, values):
            m.__dict__[self.varname] = val

        return True

    def set_register(self):
        """ Gets the value from :class:`~pypot.herkulex.motor.HkxMotor` and sets it to the specified register. """
        motors = [m for m in self.working_motors if hasattr(m, self.varname)]

        if not motors:
            return
        ids = [m.id for m in motors]

        values = (m.__dict__[self.varname] for m in motors)
        getattr(self.io, 'set_{}'.format(self.regname))(dict(list(zip(ids, values))))


class AngleLimitRegisterController(_HkxRegisterController):
    def get_register(self):
        motors = [m for m in self.working_motors if hasattr(m, self.varname)]
        if not motors:
            return

        ids = [m.id for m in motors]
        values = self.io.get_angle_limit(ids)
        print('controller getting angle limit')

        for m, val in zip(motors, values):
            m.__dict__['lower_limit'], m.__dict__['upper_limit'] = val


class _PosSpeedLoadHkxController(_HkxController):
    def setup(self):
        #dumb-down the motors to have a rectangular speed profile (like other brands)
        #self.io.set_max_accel_time(dict(zip(self.ids, itertools.repeat(0.0)))) #TODO uncomment if needed
        #
        torques = self.io.is_torque_enabled(self.ids)
        for m, c in zip(self.working_motors, torques):
            m.compliant = not c
        self._old_torques = torques

        loads = self.io.get_torque_limit(self.ids)
        goalpos = self.io.get_goal_position(self.ids)
        for m, l, p in zip(self.working_motors, loads, goalpos):
            m.__dict__['torque_limit'] = l
            m.__dict__['goal_position'] = p
        self.get_present_position_speed_load()

    def update(self):
        self.get_present_position_speed_load()
        self.set_joint_jog_load()

    def get_present_position_speed_load(self):
        values = self.io.get_present_position_speed_load(self.ids)
        if not values:
            return
        positions, speeds, loads = zip(*values)
        for m, p, s, l in zip(self.working_motors, positions, speeds, loads):
            m.__dict__['present_position'] = p
            m.__dict__['present_speed'] = s
            m.__dict__['present_load'] = l

    def set_joint_jog_load(self):
        change_torque = {}
        torques = [not m.compliant for m in self.working_motors]
        for m, t, old_t in zip(self.working_motors, torques, self._old_torques):
            if t != old_t:
                change_torque[m.id] = t
        self._old_torques = torques
        if change_torque:
            self.io._set_torque_enable(change_torque)
        rigid_motors = [m for m in self.working_motors if not m.compliant]
        ids = tuple(m.id for m in rigid_motors)
        if not ids:
            return
        #ask all motors to apply the logic required to generate a valid a jog command
        for m in rigid_motors:
            m._enforce_jog_logic()
        #only issue a jog command if the result has an exec time > 0
        values = ((m.__dict__['goal_position'],
                   m.__dict__['_exec_time'],
                   m.__dict__['torque_limit']) for m in rigid_motors if m.__dict__['_exec_time'] > 0)
        rigid_motors_to_jog = [m for m in rigid_motors if m.__dict__['_exec_time'] > 0]
        ids = tuple(m.id for m in rigid_motors_to_jog)
        self.io.set_joint_jog_load(dict(list(zip(ids, values))))
        for m in self.working_motors:
            m.__dict__['_exec_time'] = -1 #indicates that there is no outstanding jog command
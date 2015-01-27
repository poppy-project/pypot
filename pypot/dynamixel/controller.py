from ..robot.controller import MotorsController


class DxlController(MotorsController):
    """ Synchronizes the reading/writing of :class:`~pypot.dynamixel.motor.DxlMotor` with the real motors.

        This class handles synchronization loops that automatically read/write values from the "software" :class:`~pypot.dynamixel.motor.DxlMotor` with their "hardware" equivalent. Those loops shared a same :class:`~pypot.dynamixel.io.DxlIO` connection to avoid collision in the bus. Each loop run within its own thread as its own frequency.

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


class BaseDxlController(DxlController):
    """ Implements a basic controller that synchronized the most frequently used values.

    More precisely, this controller:
        * reads the present position, speed, load at 50Hz
        * writes the goal position, moving speed and torque limit at 50Hz
        * writes the pid gains (or compliance margin and slope) at 10Hz
        * reads the present voltage and temperature at 1Hz

    """
    def __init__(self, io, motors):
        factory = _DxlRegisterController

        controllers = [_PosSpeedLoadDxlController(io, motors, 50),
                       AngleLimitRegisterController(io, motors,
                                                    1, 'get', 'angle_limit'),
                       factory(io, motors, 10, 'set', 'pid_gain', 'pid'),
                       factory(io, motors, 10, 'set', 'compliance_margin'),
                       factory(io, motors, 10, 'set', 'compliance_slope'),
                       factory(io, motors, 1, 'get', 'present_voltage'),
                       factory(io, motors, 1, 'get', 'present_temperature')]

        DxlController.__init__(self, io, motors, controllers)


class _DxlController(MotorsController):
    def __init__(self, io, motors, sync_freq=50.):
        MotorsController.__init__(self, io, motors, sync_freq)

        self.ids = [m.id for m in self.working_motors]

    @property
    def working_motors(self):
        return [m for m in self.motors if not m._broken]


class _DxlRegisterController(_DxlController):
    def __init__(self, io, motors, sync_freq,
                 mode, regname, varname=None):
        _DxlController.__init__(self, io, motors, sync_freq)

        self.mode = mode
        self.regname = regname
        self.varname = regname if varname is None else varname

    def setup(self):
        if self.mode == 'set':
            self.get_register()

    def update(self):
        self.get_register() if self.mode == 'get' else self.set_register()

    def get_register(self):
        """ Gets the value from the specified register and sets it to the :class:`~pypot.dynamixel.motor.DxlMotor`. """
        motors = [m for m in self.working_motors if hasattr(m, self.varname)]
        if not motors:
            return
        ids = [m.id for m in motors]

        values = getattr(self.io, 'get_{}'.format(self.regname))(ids)
        for m, val in zip(motors, values):
            m.__dict__[self.varname] = val

    def set_register(self):
        """ Gets the value from :class:`~pypot.dynamixel.motor.DxlMotor` and sets it to the specified register. """
        motors = [m for m in self.working_motors if hasattr(m, self.varname)]

        if not motors:
            return
        ids = [m.id for m in motors]

        values = (m.__dict__[self.varname] for m in motors)
        getattr(self.io, 'set_{}'.format(self.regname))(dict(zip(ids, values)))


class AngleLimitRegisterController(_DxlRegisterController):
    def get_register(self):
        motors = [m for m in self.working_motors if hasattr(m, self.varname)]
        if not motors:
            return

        ids = [m.id for m in motors]
        values = self.io.get_angle_limit(ids)

        for m, val in zip(motors, values):
            m.__dict__['lower_limit'], m.__dict__['upper_limit'] = val


class _PosSpeedLoadDxlController(_DxlController):
    def setup(self):
        torques = self.io.is_torque_enabled(self.ids)
        for m, c in zip(self.working_motors, torques):
            m.compliant = not c
        self._old_torques = torques

        values = self.io.get_goal_position_speed_load(self.ids)
        positions, speeds, loads = zip(*values)
        for m, p, s, l in zip(self.working_motors, positions, speeds, loads):
            m.__dict__['goal_position'] = p
            m.__dict__['moving_speed'] = s
            m.__dict__['torque_limit'] = l

    def update(self):
        self.get_present_position_speed_load()
        self.set_goal_position_speed_load()

    def get_present_position_speed_load(self):
        values = self.io.get_present_position_speed_load(self.ids)

        if not values:
            return

        positions, speeds, loads = zip(*values)

        for m, p, s, l in zip(self.working_motors, positions, speeds, loads):
            m.__dict__['present_position'] = p
            m.__dict__['present_speed'] = s
            m.__dict__['present_load'] = l

    def set_goal_position_speed_load(self):
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

        values = ((m.__dict__['goal_position'],
                   m.__dict__['moving_speed'],
                   m.__dict__['torque_limit']) for m in rigid_motors)
        self.io.set_goal_position_speed_load(dict(zip(ids, values)))

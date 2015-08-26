import time

from ..robot.controller import MotorsController


class DxlController(MotorsController):
    def __init__(self, io, motors, sync_freq, synchronous,
                 mode, regname, varname=None):
        MotorsController.__init__(self, io, motors, sync_freq)

        self.ids = [m.id for m in self.working_motors]
        self.synchronous = synchronous

        self.mode = mode
        self.regname = regname
        self.varname = regname if varname is None else varname

        for m in motors:
            if mode == 'get':
                m._read_synchronous[self.varname] = self.synchronous
            else:
                m._write_synchronous[self.varname] = self.synchronous

    @property
    def working_motors(self):
        return [m for m in self.motors if not m._broken]

    @property
    def synced_motors(self):
        motors = [m for m in self.working_motors if self.varname in m.registers]

        if self.synchronous:
            motors = ([m for m in motors if m._read_synced[self.varname].needed]
                      if self.mode == 'get' else
                      [m for m in motors if m._write_synced[self.varname].needed])

        return motors

    def setup(self):
        if self.mode == 'set':
            MAX_TRIALS = 25
            for _ in range(MAX_TRIALS):
                if self.get_register(self.working_motors):
                    break
                time.sleep(0.1)
            else:
                raise IOError('Cannot initialize syncloop for "{}". You need to desactivate sync_read if you use a usb2dynamixel device. '.format(
                              self.regname))

    def update(self):
        if not self.synced_motors:
            return

        return (self.get_register(self.synced_motors)
                if self.mode == 'get' else
                self.set_register(self.synced_motors))

    def get_register(self, motors):
        """ Gets the value from the specified register and sets it to the :class:`~pypot.dynamixel.motor.DxlMotor`. """
        if not motors:
            return False

        ids = [m.id for m in motors]

        values = getattr(self.io, 'get_{}'.format(self.regname))(ids)
        if not values:
            return False

        for m, val in zip(motors, values):
            m.__dict__[self.varname] = val

        for m in motors:
            m._read_synced[self.varname].done()

        return True

    def set_register(self, motors):
        """ Gets the value from :class:`~pypot.dynamixel.motor.DxlMotor` and sets it to the specified register. """
        if not motors:
            return
        ids = [m.id for m in motors]

        values = (m.__dict__[self.varname] for m in motors)
        getattr(self.io, 'set_{}'.format(self.regname))(dict(zip(ids, values)))

        for m in motors:
            m._write_synced[self.varname].done()


class AngleLimitRegisterController(DxlController):
    def __init__(self, io, motors, sync_freq, synchronous):
        DxlController.__init__(self, io, motors, sync_freq,
                               synchronous, 'get', 'angle_limit')

        self.varnames = ['lower_limit', 'upper_limit']
        for m in motors:
            for var in self.varnames:
                m._read_synchronous[var] = self.synchronous

    @property
    def synced_motors(self):
        motors = self.working_motors

        if self.synchronous:
            sync_motors = []

            for m in motors:
                for var in self.varnames:
                    if m._read_synced[var].needed:
                        sync_motors.append(m)

            motors = sync_motors

        return motors

    def get_register(self, motors):
        if not motors:
            return

        ids = [m.id for m in motors]
        values = self.io.get_angle_limit(ids)

        for m, val in zip(motors, values):
            m.__dict__['lower_limit'], m.__dict__['upper_limit'] = val

        for m in motors:
            for var in ['lower_limit', 'upper_limit']:
                m._read_synced[var].done()


class PosSpeedLoadDxlController(DxlController):
    def __init__(self, io, motors, sync_freq):
        DxlController.__init__(self, io, motors, sync_freq,
                               False, 'get', 'present_position')

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
        self.get_present_position_speed_load(self.working_motors)
        self.set_goal_position_speed_load(self.working_motors)

    def get_present_position_speed_load(self, motors):
        ids = [m.id for m in motors]
        values = self.io.get_present_position_speed_load(ids)

        if not values:
            return

        positions, speeds, loads = zip(*values)

        for m, p, s, l in zip(motors, positions, speeds, loads):
            m.__dict__['present_position'] = p
            m.__dict__['present_speed'] = s
            m.__dict__['present_load'] = l

    def set_goal_position_speed_load(self, motors):
        change_torque = {}
        torques = [not m.compliant for m in motors]
        for m, t, old_t in zip(motors, torques, self._old_torques):
            if t != old_t:
                change_torque[m.id] = t
        self._old_torques = torques
        if change_torque:
            self.io._set_torque_enable(change_torque)

        rigid_motors = [m for m in motors if not m.compliant]
        ids = tuple(m.id for m in rigid_motors)

        if not ids:
            return

        values = ((m.__dict__['goal_position'],
                   m.__dict__['moving_speed'],
                   m.__dict__['torque_limit']) for m in rigid_motors)
        self.io.set_goal_position_speed_load(dict(zip(ids, values)))

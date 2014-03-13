import threading
import time


class DxlController(object):
    def __init__(self, dxl_io, dxl_motors):
        """ Synchronizes the reading/writing of :class:`~pypot.dynamixel.motor.DxlMotor` with the real motors.

            This class handles synchronization loops that automatically read/write values from the "software" :class:`~pypot.dynamixel.motor.DxlMotor` with their "hardware" equivalent. Those loops shared a same :class:`~pypot.dynamixel.io.DxlIO` connection to avoid collision in the bus. Each loop run within its own thread at its own frequency.

            .. warning:: As all the loop attached to a controller shared the same bus, you should make sure that they can run without slowing down the other ones.

            """
        self._dxl_io = dxl_io

        self._motors = dxl_motors
        self._ids = tuple(m.id for m in self._motors)

        self._loops = []

    def __del__(self):
        self.close()

    def __exit__(self):
        self.close()

    def close(self):
        self.stop()
        self._dxl_io.close()

    def start(self):
        """ Starts all the synchronization loops. """
        for l in self._loops:
            l.start()
            l._started.wait()

    def stop(self):
        """ Stops al the synchronization loops (they can not be started again). """
        for l in filter(lambda l: l.is_alive(), self._loops):
                l.stop()
                l.join()

    def add_sync_loop(self, freq, function, name):
        """ Adds a synchronization loop that will run a function at a predefined freq. """
        sl = _RepeatedTimer(freq, function, name)
        self._loops.append(sl)

    def add_read_loop(self, freq, regname, varname=None):
        """ Adds a read loop that will get the value from the specified register and set it to the :class:`~pypot.dynamixel.motor.DxlMotor`. """
        varname = varname if varname else regname
        self.add_sync_loop(freq, lambda: self._get_register(regname, varname),
                           'Thread-get_{}'.format(regname))

    def _get_register(self, regname, varname):
        motors = [m for m in self._motors if hasattr(m, varname)]
        if not motors:
            return
        ids = [m.id for m in motors]

        values = getattr(self._dxl_io, 'get_{}'.format(regname))(ids)
        for m, val in zip(motors, values):
            m._values[varname] = val

    def add_write_loop(self, freq, regname, varname=None):
        """ Adds a write loop that will get the value from :class:`~pypot.dynamixel.motor.DxlMotor` and set it to the specified register. """
        varname = varname if varname else regname

        # We force a get to initalize the synced var to their current values
        self._get_register(regname, varname)

        self.add_sync_loop(freq, lambda: self._set_register(regname, varname),
                           'Thread-set_{}'.format(regname))

    def _set_register(self, regname, varname):
        motors = [m for m in self._motors if hasattr(m, varname)]

        if not motors:
            return
        ids = [m.id for m in motors]

        values = (m._values[varname] for m in motors)
        getattr(self._dxl_io, 'set_{}'.format(regname))(dict(zip(ids, values)))


class BaseDxlController(DxlController):
    """ Implements a basic controller that synchronized the most frequently used values.

        More precisely, this controller:
            * reads the present position, speed, load at 50Hz
            * writes the goal position, moving speed and torque limit at 50Hz
            * writes the pid gains (or compliance margin and slope) at 10Hz
            * reads the present voltage and temperature at 1Hz

        """
    def __init__(self, dxl_io, dxl_motors):
        DxlController.__init__(self, dxl_io, dxl_motors)

        self.add_sync_loop(50, self._get_pos_speed_load, 'Thread-get_pos_speed_load')
        self.add_sync_loop(50, self._set_pos_speed_load, 'Thread-set_pos_speed_load')

        self.add_write_loop(10, 'pid_gain', 'pid')
        self.add_write_loop(10, 'compliance_margin')
        self.add_write_loop(10, 'compliance_slope')

        self.add_read_loop(1, 'angle_limit')
        self.add_read_loop(1, 'present_voltage')
        self.add_read_loop(1, 'present_temperature')

        torques = self._dxl_io.is_torque_enabled(self._ids)
        for m, c in zip(self._motors, torques):
            m.compliant = not c
        self._old_torques = torques

        values = self._dxl_io.get_goal_position_speed_load(self._ids)
        positions, speeds, loads = zip(*values)
        for m, p, s, l in zip(self._motors, positions, speeds, loads):
            m._values['goal_position'] = p
            m._values['moving_speed'] = s
            m._values['torque_limit'] = l

    def _get_pos_speed_load(self):
        values = self._dxl_io.get_present_position_speed_load(self._ids)

        if not values:
            return

        positions, speeds, loads = zip(*values)

        for m, p, s, l in zip(self._motors, positions, speeds, loads):
            m._values['present_position'] = p
            m._values['present_speed'] = s
            m._values['present_load'] = l

    def _set_pos_speed_load(self):
        change_torque = {}
        torques = [not m.compliant for m in self._motors]
        for m, t, old_t in zip(self._motors, torques, self._old_torques):
            if t != old_t:
                change_torque[m.id] = t
        self._old_torques = torques
        if change_torque:
            self._dxl_io._set_torque_enable(change_torque)

        rigid_motors = [m for m in self._motors if not m.compliant]
        ids = tuple(m.id for m in rigid_motors)

        if not ids:
            return

        values = ((m._values['goal_position'],
                   m._values['moving_speed'],
                   m._values['torque_limit']) for m in rigid_motors)
        self._dxl_io.set_goal_position_speed_load(dict(zip(ids, values)))


class _RepeatedTimer(threading.Thread):
    def __init__(self, freq, function, name=None):
        threading.Thread.__init__(self, name=name)
        self.daemon = True

        self.period = 1.0 / freq
        self.function = function

        self._running = threading.Event()
        self._running.set()

        self._started = threading.Event()

    def run(self):
        while self._running.is_set():
            start = time.time()

            self.function()

            if not self._started.is_set():
                self._started.set()

            end = time.time()

            st = self.period - (end - start)
            if st > 0:
                time.sleep(st)

    def stop(self):
        self._running.clear()

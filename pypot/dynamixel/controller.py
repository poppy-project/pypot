import threading
import time


class DynamixelController(object):
    def __init__(self, dxl_io, dxl_motors):
        self._dxl_io = dxl_io
        
        self._motors = dxl_motors
        self._ids = tuple(m.id for m in self._motors)

        self._loops = []

    def start(self):
        map(_RepeatedTimer.start, self._loops)

    def stop(self):
        map(_RepeatedTimer.stop, self._loops)
    
            
    def add_sync_loop(self, freq, function, name):
        sl = _RepeatedTimer(freq, function, name)
        self._loops.append(sl)

    def add_read_loop(self, freq, regname, varname=None):
        varname = varname if varname else regname
        self.add_sync_loop(freq, lambda: self._get_register(regname, varname),
                           'Thread-get_{}'.format(regname))
    
    def _get_register(self, regname, varname):
        values = getattr(self._dxl_io, 'get_{}'.format(regname))(*self._ids)
        for m, val in zip(self._motors, values):
            m._values[varname] = val

    def add_write_loop(self, freq, regname, varname=None):
        varname = varname if varname else regname

        # We force a get to initalize the synced var to their current values
        self._get_register(regname, varname)
        
        self.add_sync_loop(freq, lambda: self._set_register(regname, varname),
                           'Thread-set_{}'.format(regname))

    def _set_register(self, regname, varname):
        values = (m._values[varname] for m in self._motors)
        getattr(self._dxl_io, 'set_{}'.format(regname))(dict(zip(self._ids, values)))


class BaseDynamixelController(DynamixelController):
    def __init__(self, dxl_io, dxl_motors):
        DynamixelController.__init__(self, dxl_io, dxl_motors)
        
        self.add_sync_loop(50, self._get_pos_speed_load, 'Thread-get_pos_speed_load')
        self.add_sync_loop(50, self._set_pos_speed_load, 'Thread-set_pos_speed_load')

        self.add_write_loop(10, 'pid_gain', 'pid')

        self.add_read_loop(1, 'present_voltage')
        self.add_read_loop(1, 'present_temperature')
    
        values = self._dxl_io.get_goal_position_speed_load(*self._ids)
        positions, speeds, loads = zip(*values)
        for m, p, s, l in zip(self._motors, positions, speeds, loads):
            m._values['goal_position'] = p
            m._values['moving_speed'] = s
            m._values['torque_limit'] = l

    def _get_pos_speed_load(self):
        values = self._dxl_io.get_present_position_speed_load(*self._ids)
        positions, speeds, loads = zip(*values)

        for m, p, s, l in zip(self._motors, positions, speeds, loads):
            m._values['present_position'] = p
            m._values['present_speed'] = s
            m._values['present_load'] = l

    def _set_pos_speed_load(self):
        values = ((m._values['goal_position'],
                   m._values['moving_speed'],
                   m._values['torque_limit']) for m in self._motors)
        
        self._dxl_io.set_goal_position_speed_load(dict(zip(self._ids, values)))


class _RepeatedTimer(threading.Thread):
    def __init__(self, freq, function, name=None):
        threading.Thread.__init__(self, name=name)
        self.daemon = True
        
        self.period = 1.0 / freq
        self.function = function

        self._running = threading.Event()
        self._running.set()

    def run(self):
        while self._running.is_set():
            start = time.time()
            self.function()
            end = time.time()

            st = self.period - (end - start)
            if st > 0:
                time.sleep(st)

    def stop(self):
        self._running.clear()
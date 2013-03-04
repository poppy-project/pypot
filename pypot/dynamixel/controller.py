import threading
import time


class DxlController(object):
    def __init__(self, dxl_io, dxl_motors):
        self._dxl_io = dxl_io
        
        self._motors = dxl_motors
        self._ids = tuple(m.id for m in self._motors)

        self._loops = []

    def start(self):
        for l in self._loops:
            l.start()
            l._started.wait()    

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
        motors = filter(lambda m: hasattr(m, varname), self._motors)
        if not motors:
            return
        ids = [m.id for m in motors]
        
        values = getattr(self._dxl_io, 'get_{}'.format(regname))(ids)
        for m, val in zip(motors, values):
            m._values[varname] = val

    def add_write_loop(self, freq, regname, varname=None):
        varname = varname if varname else regname

        # We force a get to initalize the synced var to their current values
        self._get_register(regname, varname)
        
        self.add_sync_loop(freq, lambda: self._set_register(regname, varname),
                           'Thread-set_{}'.format(regname))

    def _set_register(self, regname, varname):
        motors = filter(lambda m: hasattr(m, varname), self._motors)
        if not motors:
            return
        ids = [m.id for m in motors]
        
        values = (m._values[varname] for m in motors)
        getattr(self._dxl_io, 'set_{}'.format(regname))(dict(zip(ids, values)))


class BaseDxlController(DxlController):
    def __init__(self, dxl_io, dxl_motors):
        DxlController.__init__(self, dxl_io, dxl_motors)
        
        self.add_sync_loop(50, self._get_pos_speed_load, 'Thread-get_pos_speed_load')
        self.add_sync_loop(50, self._set_pos_speed_load, 'Thread-set_pos_speed_load')

        self.add_write_loop(10, 'pid_gain', 'pid')
        self.add_write_loop(10, 'compliance_margin')
        self.add_write_loop(10, 'compliance_slope')

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
        torques = map(lambda m: not m.compliant, self._motors)
        for m, t, old_t in zip(self._motors, torques, self._old_torques):
            if t != old_t:
                change_torque[m.id] = t
        self._old_torques = torques
        if change_torque:
            self._dxl_io._set_torque_enable(change_torque)
    
        rigid_motors = filter(lambda m: not m.compliant, self._motors)
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

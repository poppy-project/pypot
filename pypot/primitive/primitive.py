import time
import threading

import pypot.dynamixel



class Primitive(object):
    def __init__(self, robot, *args, **kwargs):
        self.robot = MockupRobot(robot)
        
        self.args = args
        self.kwargs = kwargs
        
        self._stop = threading.Event()
        self._resume = threading.Event()
    
    def _wrapped_run(self):
        self.t0 = time.time()
        self.run(*self.args, **self.kwargs)
        self.robot._primitive_manager.remove(self)

    def run(self, *args, **kwargs):
        pass
    
    @property
    def elapsed_time(self):
        return time.time() - self.t0

    # MARK: - Start/Stop handling
    
    def start(self):
        if self.is_alive():
            self.stop()
            self._thread.join()

        self._resume.set()
        self._stop.clear()

        self.robot._primitive_manager.add(self)

        self._thread = threading.Thread(target=self._wrapped_run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        self._stop.set()
    
    def should_stop(self):
        return self._stop.is_set()
    
    def is_alive(self):
        return hasattr(self, '_thread') and self._thread.is_alive()
    
    # MARK: - Pause/Resume handling
    
    def pause(self):
        self._resume.clear()
    
    def resume(self):
        self._resume.set()
    
    def should_pause(self):
        return not self._resume.is_set()

    def wait_to_resume(self):
        self._resume.wait()

class LoopPrimitive(Primitive):
    def __init__(self, robot, freq, *args, **kwargs):
        Primitive.__init__(self, robot, *args, **kwargs)
        self.period = 1.0 / freq

    def run(self, *args, **kwargs):        
        while not self.should_stop():
            if self.should_pause():
                self.wait_to_resume()

            start = time.time()
            self.update(*self.args, **self.kwargs)
            end = time.time()

            dt = self.period - (end - start)
            if dt > 0:
                time.sleep(dt)    

    def update(self, t, *args, **kwargs):
        raise NotImplementedError


class MockupRobot(object):
    def __init__(self, robot):
        self._robot = robot
        self._motors = []
        
        for m in robot.motors:
            mockup_motor = MockupMotor(m)
            self._motors.append(mockup_motor)
            setattr(self, m.name, mockup_motor)
    
    def __getattr__(self, attr):
        return getattr(self._robot, attr)
    
    @property
    def motors(self):
        return self._motors


class MockupMotor(pypot.dynamixel.DxlMotor):
    def __init__(self, m):
        pypot.dynamixel.DxlMotor.__init__(self, m.id, m.name, m.direct, m.offset)
        self._values = m._values
        self.to_set = {}
    
    @property
    def goal_position(self):
        return pypot.dynamixel.DxlMotor.goal_position.fget(self)
    
    @goal_position.setter
    def goal_position(self, value):
        self.to_set['goal_position'] = value
    
    @property
    def moving_speed(self):
        return pypot.dynamixel.DxlMotor.moving_speed.fget(self)
    
    @moving_speed.setter
    def moving_speed(self, value):
        self.to_set['moving_speed'] = value
    
    @property
    def torque_limit(self):
        return pypot.dynamixel.DxlMotor.torque_limit.fget(self)
    
    @torque_limit.setter
    def torque_limit(self, value):
        self.to_set['torque_limit'] = value
    
    @property
    def pid(self):
        return pypot.dynamixel.DxlMotor.pid.fget(self)
    
    @pid.setter
    def pid(self, value):
        self.to_set['pid'] = value
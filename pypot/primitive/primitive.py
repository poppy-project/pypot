import threading
import time


class Primitive(object):
    def __init__(self, frequency):
        self.thread = None
        
        self._running = False
        self._paused = False

        self.period = 1.0 / frequency
    
        self._modified_values = {}
    
    
    # MARK: - Event handling
    
    def start(self):
        if self.is_running():
            self.stop()
        
        self._running = True

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    
    def stop(self):
        self._running = False

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def is_running(self):
        return self._running
    

    # MARK: - Main Loop

    def run(self):
        self.set_up()
        
        while self._running:
            dt = self.period
            
            if not self._paused:
                start = time.time()
                self.update()
                end = time.time()
            
                dt -= (end - start)

            if dt > 0:
                time.sleep(dt)

        self.tear_down()

    # MARK: - 
    
    def set_up(self):
        pass

    def update(self):
        pass

    def tear_down(self):
        pass

    def get_modified_values(self):
        return self._modified_values


class PlayMotion(Primitive):
    def __init__(self, frequency, motion):
        Primitive.__init__(self, frequency)
        self.motion = motion
        self.i = 0

    def set_up(self):
        self.i = 0
        self._modified_values['motor_1'] = {}

    def update(self):
        x = self.motion[self.i]
        self.i += 1
        
        self._modified_values['motor_1']['goal_position'] = x

        if self.i >= len(self.motion):
            self.stop()

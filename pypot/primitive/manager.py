import threading
import numpy
import time

from collections import defaultdict

class PrimitiveManager(threading.Thread):
    def __init__(self, motors, freq=50, filter=numpy.mean):
        threading.Thread.__init__(self, name='Primitive Manager')
        self.daemon = True
        
        self._prim = []
        self._period = 1.0 / freq
        self._motors = motors
        self._filter = filter
        self._running = threading.Event()
        self._running.set()

    def add(self, p):
        self._prim.append(p)

    def remove(self, p):
        self._prim.remove(p)
    
    @property
    def primitives(self):
        return self._prim

    def run(self):
        while self._running.is_set():
            start = time.time()
            
            for m in self._motors:
                to_set = defaultdict(list)

                for p in self._prim:
                    for key, val in getattr(p.robot, m.name).to_set.iteritems():
                        to_set[key].append(val)
        
                for key, val in to_set.iteritems():
                    filtred_val = self._filter(val)
                    setattr(m, key, filtred_val)
            
            end = time.time()
            
            dt = self._period - (end - start)
            if dt > 0:
                time.sleep(dt)

    def stop(self):
        self._running.clear()
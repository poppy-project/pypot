import time
import cPickle
import scipy.io
import threading

from itertools import cycle
import pypot.primitive


class Move(object):
    def __init__(self):
        self._pos = []
    
    def __iter__(self):
        return self.pos.__iter__()
    
    def next(self):
        return self.pos.next()
    
    def add_position(self, dt, position):
        self._pos.append((dt, position))
    
    def save(self, filename):
        cPickle.dump(self, open(filename, 'w'))
    
    @classmethod
    def load(cls, filename):
        return cPickle.load(open(filename))

    @property
    def pos(self):
        return self._pos

class MoveRecorder(pypot.primitive.Primitive):
    def __init__(self, robot, tracked_motors, compliant=False):
        pypot.primitive.Primitive.__init__(self, robot)
        
        self.tracked_motors = map(self._get_mockup_motor, tracked_motors)
        self._move = Move()
        self.compliant = compliant
        
        self.should_snap = threading.Event()
    
    def start(self):
        if hasattr(self, 't0'):
            del self.t0
        self._move = Move()
        pypot.primitive.Primitive.start(self)

    def add_keyframe(self):
        self.should_snap.set()
    
    def run(self):
        if self.compliant:
            for m in self.tracked_motors:
                m.compliant = True
                    
        while not self.should_stop():
            self.should_snap.wait()
            
            pos = dict((m.name, m.present_position) for m in self.tracked_motors)

            if not hasattr(self, 't0'):
                self.t0 = time.time()
        
            dt = time.time() - self.t0
            self._move.add_position(dt, pos)
            
            self.should_snap.clear()

        if self.compliant:
            for m in self.tracked_motors:
                m.compliant = False    
    
    @property
    def move(self):
        return self._move

class LoopMoveRecorder(pypot.primitive.LoopPrimitive):
    def __init__(self, robot, freq, tracked_motors, compliant=False):
        pypot.primitive.LoopPrimitive.__init__(self, robot, freq)
        self.move_recorder = MoveRecorder(robot, tracked_motors, compliant)

    def start(self):
        pypot.primitive.LoopPrimitive.start(self)
        self.move_recorder.start()

    def update(self):
        self.move_recorder.add_keyframe()

    @property
    def move(self):
        return self.move_recorder.move


class MovePlayer(pypot.primitive.Primitive):
    def __init__(self, robot, move):
        pypot.primitive.Primitive.__init__(self, robot)
        self.move = move
    
    def play(self):
        self.start()
    
    def run(self):
        last_t = 0
        
        for t, pos in self.move:
            if self.should_stop():
                break
            
            if self.should_pause():
                self.wait_to_resume()
            
            dt = t - last_t
            self.robot.goto_position(pos, dt, wait=True)
                    
            last_t = t

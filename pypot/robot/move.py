import json

from pypot.primitive import LoopPrimitive


class Move(dict):
    def __init__(self, framerate):
        self['framerate'] = framerate
        self['position'] = []
        self._iter = iter(self['position'])

    def add_position(self, position):
        self['position'].append(position)

    def next(self):
        return self._iter.next()

    def save(self, file):
        json.dump(self, file)

    @classmethod
    def load(cls, file):
        d = json.load(file)
        m = cls(d['framerate'])
        m['position'] = d['position']
        return m

class MoveRecorder(LoopPrimitive):
    def __init__(self, robot, freq, tracked_motors):
        LoopPrimitive.__init__(self, robot, freq)
        self.move = Move(freq)

        self.tracked_motors = map(self.get_mockup_motor, tracked_motors)


    def update(self):
        LoopPrimitive.update(self)

        position = dict(zip([(m.present_position, m.name) for m in self.tracked_motors]))
        self.move.add_position(position)


class MovePlayer(LoopPrimitive):
    def __init__(self, robot, freq, move):
        LoopPrimitive.__init__(self, robot, freq)
        self.move = move

    def update(self):
        LoopPrimitive.update(self)

        position = self.move.next()
        for m, v in position.iteritems():
            getattr(self.robot, m).goal_position = v

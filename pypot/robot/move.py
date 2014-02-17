import json

from pypot.primitive import LoopPrimitive


class Move(dict):
    def __init__(self, freq):
        dict.__init__(self, {'framerate': freq,
                             'position': []})

    def add_position(self, position):
        self['position'].append(position)

    def positions(self):
        return iter(self['position'])

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
        self._move = Move(freq)

        self.tracked_motors = map(self.get_mockup_motor, tracked_motors)

    def update(self):
        LoopPrimitive.update(self)

        position = dict([(m.name, m.present_position) for m in self.tracked_motors])
        self._move.add_position(position)

    @property
    def move(self):
        return self._move


class MovePlayer(LoopPrimitive):
    def __init__(self, robot, move):
        LoopPrimitive.__init__(self, robot, move['framerate'])
        self.move = move

    def start(self):
        self.positions = self.move.positions()
        LoopPrimitive.start(self)

    def update(self):
        LoopPrimitive.update(self)

        try:
            position = self.positions.next()

            for m, v in position.iteritems():
                getattr(self.robot, m).goal_position = v

        except StopIteration:
            self.stop()

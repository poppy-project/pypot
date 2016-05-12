from __future__ import division

import json
import time
import logging
import numpy as np

from .primitive import LoopPrimitive
from pypot.utils.interpolation import KDTreeDict
logger = logging.getLogger(__name__)


class Move(object):

    """ Simple class used to represent a movement.

    This class simply wraps a sequence of positions of specified motors. The sequence must be recorded at a predefined frequency. This move can be recorded through the :class:`~pypot.primitive.move.MoveRecorder` class and played thanks to a :class:`~pypot.primitive.move.MovePlayer`.

    """

    def __init__(self, freq):
        self._framerate = freq
        self._timed_positions = KDTreeDict()

    def __repr__(self):
        return '<Move framerate={} #keyframes={}>'.format(self.framerate,
                                                          len(self.positions()))

    def __getitem__(self, i):
        return list(self._timed_positions.items())[i]

    @property
    def framerate(self):
        return self._framerate

    def add_position(self, pos, time):
        """ Add a new position to the movement sequence.

        Each position is typically stored as a dict of (time, (motor_name,motor_position)).
        """
        self._timed_positions[time] = pos

    def iterpositions(self):
        """ Returns an iterator on the stored positions. """
        return self._timed_positions.items()

    def positions(self):
        """ Returns a copy of the stored positions. """
        return self._timed_positions

    def plot(self, ax):
        pos = self.positions()

        if not pos:
            return

        motors = pos[0].keys()

        n = len(pos)
        t = np.linspace(0, n / self.framerate, n)
        pos = self.positions()

        p = {}
        for name in motors:
            p[name] = []

        for tt in t:
            for k, v in pos[float(tt)].items():
                p[k].append(v[0])

        for name in motors:
            ax.plot(t, p[name])

        ax.legend(motors)
        ax.set_xlabel('Time (in s)')
        ax.set_ylabel('Position (in degree)')

    def save(self, file):
        """ Saves the :class:`~pypot.primitive.move.Move` to a json file.

        .. note:: The format used to store the :class:`~pypot.primitive.move.Move` is extremely verbose and should be obviously optimized for long moves.
        """
        d = {
            'framerate': self.framerate,
            'positions': self._timed_positions,
        }
        json.dump(d, file, indent=2)

    @classmethod
    def create(cls, d):
        """ Create a :class:`~pypot.primitive.move.Move` from a dictionary. """
        move = cls(d['framerate'])
        move._timed_positions.update(d['positions'])
        return move

    @classmethod
    def load(cls, file):
        """ Loads a :class:`~pypot.primitive.move.Move` from a json file. """
        d = json.load(file)
        return cls.create(d)

    @classmethod
    def loads(cls, str):
        """ Loads a :class:`~pypot.primitive.move.Move` from a json string. """
        d = json.loads(str)
        return cls.create(d)


class MoveRecorder(LoopPrimitive):

    """ Primitive used to record a :class:`~pypot.primitive.move.Move`.

    The recording can be :meth:`~pypot.primitive.primitive.Primitive.start` and :meth:`~pypot.primitive.primitive.Primitive.stop` by using the :class:`~pypot.primitive.primitive.LoopPrimitive` methods.

    .. note:: Re-starting the recording will create a new :class:`~pypot.primitive.move.Move` losing all the previously stored data.

    """

    def __init__(self, robot, freq, tracked_motors):
        LoopPrimitive.__init__(self, robot, freq)
        self.freq = freq
        self.tracked_motors = map(self.get_mockup_motor, tracked_motors)

    def setup(self):
        self._move = Move(self.freq)

    def update(self):
        position = dict([(m.name, (m.present_position, m.present_speed))
                         for m in self.tracked_motors])
        self._move.add_position(position, self.elapsed_time)

    @property
    def move(self):
        """ Returns the currently recorded :class:`~pypot.primitive.move.Move`. """
        return self._move

    def add_tracked_motors(self, tracked_motors):
        """Add new motors to the recording"""
        new_mockup_motors = map(self.get_mockup_motor, tracked_motors)
        self.tracked_motors = list(set(self.tracked_motors + new_mockup_motors))


class MovePlayer(LoopPrimitive):

    """ Primitive used to play a :class:`~pypot.primitive.move.Move`.

    The playing can be :meth:`~pypot.primitive.primitive.Primitive.start` and :meth:`~pypot.primitive.primitive.Primitive.stop` by using the :class:`~pypot.primitive.primitive.LoopPrimitive` methods.

    .. warning:: the primitive is run automatically the same framerate than the move record.
        The play_speed attribute change only time lockup/interpolation
    """

    def __init__(self, robot, move=None, play_speed=1.0, move_filename=None, start_max_speed=50, **kwargs):
        self.move = move
        self.backwards = False
        if move_filename is not None:
            with open(move_filename, 'r') as f:
                self.move = Move.load(f)
        self.play_speed = play_speed if play_speed != 0 and isinstance(play_speed, float) else 1.0
        framerate = self.move.framerate if self.move is not None else 50.0
        self.start_max_speed = start_max_speed if start_max_speed != 0 else np.inf
        for key, value in kwargs.items():
            setattr(self, key, value)
        LoopPrimitive.__init__(self, robot, framerate)

    def setup(self):
        if self.move is None:
            raise AttributeError("Attribute move is not defined")
        self.period = 1.0 / self.move.framerate
        self.positions = self.move.positions()
        self.__duration = self.duration()
        if self.play_speed < 0:
            self.play_speed = - self.play_speed
            self.backwards = not self.backwards
        if self.play_speed == 0:
            self.play_speed = 1.0

        # Quick fix for limiting too fast movements at the play start
        max_goto_time = 0
        if self.backwards:
            position = self.positions[self.__duration]
        else:
            position = self.positions[0]
        for motor, value in position.iteritems():
            motor = getattr(self.robot, motor)
            motor.compliant = False
            delta_angle = abs(motor.present_position - value[0])
            if delta_angle > 5:
                goto_time = delta_angle / self.start_max_speed
                motor.goto_position(value[0], goto_time)
                max_goto_time = goto_time if goto_time > max_goto_time else max_goto_time

        time.sleep(max_goto_time)

    def update(self):
        if self.elapsed_time < self.__duration:
            if self.backwards:
                position = self.positions[(self.__duration - self.elapsed_time) * self.play_speed]
            else:
                position = self.positions[self.elapsed_time * self.play_speed]

            for motor, value in position.iteritems():
                # TODO: Ask pierre if its not a fgi to turn off the compliance
                getattr(self.robot, motor).compliant = False
                getattr(self.robot, motor).goal_position = value[0]
        else:
            self.stop()

    def duration(self):

        if self.move is not None:
            return (len(self.move.positions()) / self.move.framerate) / self.play_speed
        else:
            return 1.0

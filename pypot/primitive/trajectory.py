import numpy
import time


class Trajectory(object):
    """ Represents a trajectory composed of keyframes of motor(s).

    Each keyframe is composed of the timestamp and the position of each recorded motor.

    .. note:: The timestamp is defined relatively to the first recorded keyframe.

    """
    def __init__(self, motor_names):
        self._motors = motor_names
        self._positions = []
        self._timestamps = []

    def __repr__(self):
        n = len(self._timestamps)
        return '<Trajectory motors={} #keyframe{}={}>'.format(self.motors,
                                                              's' if n > 1 else '',
                                                              n)

    def __getitem__(self, i):
        """ Returns the ith keyframe.

         .. note:: For performance issue you should not iterate over keyframes using __getitem__.

         # TODO: We most likely should remove this as this is clearly not efficient way of accessing key frames.
        """
        return self.keyframes[i]

    @property
    def motors(self):
        return self._motors

    @property
    def timestamps(self):
        """ Returns an 1D array of the timestamps of the positions. """
        return numpy.array(self._timestamps)

    @property
    def positions(self):
        """ Returns an (N, M) shaped array of the positions of the motors.

        N is the number of positions recorded.
        M is the number of motors.
        """
        return numpy.array(self._positions)

    @property
    def keyframes(self):
        """ Returns an array of (timestamp, position) """
        return numpy.hstack((self.timestamps.reshape((-1, 1)),
                             self.positions))

    def iterkeyframes(self):
        """ Returns an iterator on the stored keyframes. """
        # TODO: Does it make sense ?
        # As we compute the whole keyframes array to return the iterator ???
        return iter(self.keyframes)

    def add_keyframe(self, positions):
        """ Add a new position to the trajectory.

        Each position is a vector of M positions (M is the number of motor recorded in the trajectory).
        """
        if len(positions) != len(self.motors):
            msg = 'The given position was not the desired length ({} != {})'.format(len(positions), len(self.motors))
            raise ValueError(msg)

        self._timestamps.append(self._current_time)
        self._positions.append(positions)

    def save(self, file):
        numpy.savez(file,
                    motors=self.motors,
                    keyframes=self.keyframes)

    @classmethod
    def load(cls, file):
        # TODO What happened with t0 when loading ????
        # We should prevent from adding keyframes to a load trajectory ???
        npzfile = numpy.load(file)

        trajectory = cls(npzfile['motors'].tolist())
        keyframes = npzfile['keyframes']

        trajectory._timestamps = keyframes[:, 0].tolist()
        trajectory._positions = keyframes[:, 1:].tolist()
        return trajectory

    @property
    def _current_time(self):
        if not hasattr(self, '_t0'):
            self._t0 = time.time()
            return 0.0

        return time.time() - self._t0


if __name__ == '__main__':
    import random
    import matplotlib.pyplot as plt

    motors = ['m0', 'm1', 'm2']
    t = Trajectory(motors)

    t.add_keyframe([0] * 3)

    print t

    t.add_keyframe(range(3))

    print t

    for _ in range(10):
        time.sleep(random.random() / 10)
        pos = [random.random() for _ in range(3)]
        t.add_keyframe(pos)

    print t

    plt.plot(t.keyframes[:, 0], t.keyframes[:, 1:])
    plt.legend(motors)
    plt.show()

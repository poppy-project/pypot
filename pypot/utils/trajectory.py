from __future__ import division

import numpy
import collections

import pypot.utils.pypot_time as time
from ..utils.stoppablethread import StoppableLoopThread


class MinimumJerkTrajectory(object):
    def __init__(self, initial, final, duration, init_vel=0.0, init_acc=0.0, final_vel=0.0, final_acc=0.0):
        self.initial = initial
        self.final = final
        self.duration = duration
        self.init_vel = init_vel
        self.init_acc = init_acc
        self.final_vel = final_vel
        self.final_acc = final_acc

        self.durations = [0, duration]
        self.finals = [final]

        self.compute()

    def compute(self):  # N'Guyen's magic
        a0 = self.initial
        a1 = self.init_vel
        a2 = self.init_acc / 2.0
        d = lambda x: self.duration ** x

        A = numpy.array([[d(3), d(4), d(5)], [3 * d(2), 4 * d(3), 5 * d(4)], [6 * d(1), 12 * d(2), 20 * d(3)]])
        B = numpy.array([self.final - a0 - (a1 * d(1)) - (a2 * d(2)), self.final_vel - a1 - (2 * a2 * d(1)), self.final_acc - (2 * a2)])
        X = numpy.linalg.solve(A, B)

        self.other_gen = None

        self._mylambda = lambda x: a0 + a1 * x + a2 * x ** 2 + X[0] * x ** 3 + X[1] * x ** 4 + X[2] * x ** 5

        self._generators = [self._mylambda]

    def get_value(self, t):
        return self._mygenerator[-1](t)

    def domain(self, x):
        if not isinstance(x, collections.Iterable):
            x = numpy.array([x])

        domain = []
        for d in range(len(self.durations) - 1):
            d1 = []
            for xi in x:
                d1.append(
                    (xi >= self.durations[d]) & (xi < self.durations[d + 1]))
            domain.append(numpy.array(d1))

        return numpy.array(domain)

    def test_domain(self, x):
        return [((numpy.array(x) >= self.durations[i])) for i in range(len(self.durations) - 1)]

    def fix_input(self, x):
        return x if isinstance(x, collections.Iterable) else numpy.array([0, x])

    def get_generator(self):
        return lambda x: numpy.piecewise(x, self.domain(x), [self._generators[j] for j in range(len(self._generators))] + [self.finals[-1]])


class GotoMinJerk(StoppableLoopThread):
    def __init__(self, motor, position, duration, frequency=50):
        StoppableLoopThread.__init__(self, frequency)

        self.motor = motor
        self.goal = position  # dict { 'motor1_name': x1, 'motor2_name': x2 }
        self.duration = duration  # seconds

    def setup(self):
        if self.duration < numpy.finfo(float).eps:
            self.motor.goal_position = self.goal
            self.stop()
        else:
            self.trajs = MinimumJerkTrajectory(self.motor.present_position, self.goal, self.duration).get_generator()
        self.t0 = time.time()

    def update(self):
        if numpy.finfo(float).eps < self.duration > self.elapsed_time:
            self.motor.goal_position = self.trajs(self.elapsed_time)
        else:
            self.stop(wait=False)

    @property
    def elapsed_time(self):
        return time.time() - self.t0

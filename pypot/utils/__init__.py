from collections import namedtuple
from operator import attrgetter
from threading import Event

from .stoppablethread import StoppableThread, StoppableLoopThread
from .pypot_time import time

Point2D = namedtuple('Point2D', ('x', 'y'))
Point3D = namedtuple('Point3D', ('x', 'y', 'z'))
Point = Point3D

Vector3D = namedtuple('Vector3D', ('x', 'y', 'z'))
Vector = Vector3D

Quaternion = namedtuple('Quaternion', ('x', 'y', 'z', 'w'))


def attrsetter(item):
    def resolve_attr(obj, attr):
        if not attr:
            return obj
        for name in attr.split('.'):
            obj = getattr(obj, name)
        return obj

    def g(obj, value):
        var_path, _, var_name = item.rpartition('.')
        setattr(resolve_attr(obj, var_path), var_name, value)

    return g


class SyncEvent(object):
    def __init__(self, period=.1):
        self._event = Event()
        self._needed = False

        self._last_sync = 0.
        self.period = period

    def request(self):
        self._needed = True
        self._event.wait()
        self._event.clear()

    def done(self):
        self._event.set()
        self._last_sync = time()
        self._needed = False

    @property
    def is_recent(self):
        return (time() - self._last_sync) < self.period

    @property
    def needed(self):
        return self._needed and not self.is_recent

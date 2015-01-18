from collections import namedtuple
from operator import attrgetter

from .stoppablethread import StoppableThread, StoppableLoopThread


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

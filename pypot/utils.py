from collections import namedtuple

Point2D = namedtuple('Point2D', ('x', 'y'))
Point3D = namedtuple('Point3D', ('x', 'y', 'z'))
Point = Point3D

Vector3D = namedtuple('Vector3D', ('x', 'y', 'z'))
Vector = Vector3D

Quaternion = namedtuple('Quaternion', ('x', 'y', 'z', 'w'))
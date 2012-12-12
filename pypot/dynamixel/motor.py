from collections import defaultdict
from operator import getitem, setitem


from pypot.robot.motor import Motor



class DynamixelMotor(Motor):
    def __init__(self, id):
        self._id = id
        self._values = defaultdict(int)
    
    def __repr__(self):
        return '<Motor id={self.id} pos={self.position}>'.format(self=self)

    def _make_accessor(name, rw=False):
        return property(fget=lambda self: getitem(self._values, name),
                        fset=(lambda self, value: setitem(self._values, name, value)) if rw else None)

    @property
    def id(self):
        return self._id

    present_position = _make_accessor('present_position')
    present_speed = _make_accessor('present_speed')
    present_load = _make_accessor('present_load')

    goal_position = _make_accessor('goal_position', rw=True)
    moving_speed = _make_accessor('moving_speed', rw=True)
    torque_limit = _make_accessor('torque_limit', rw=True)

    pid = _make_accessor('pid', rw=True)

    present_voltage = _make_accessor('present_voltage')
    present_temperature = _make_accessor('present_temperature')

    @property
    def position(self):
        return self.present_position

    @position.setter
    def position(self, value):
        self.goal_position = value


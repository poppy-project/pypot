import time
import numpy

from collections import defaultdict
from operator import getitem, setitem


class DxlMotor(object):
    def __init__(self, id, name=None,
                 direct=True, offset=0.0):
        self._id = id
        self._name = name if name else 'motor_{}'.format(id)
        
        self._direct = direct
        self._offset = offset
    
        self._values = defaultdict(int)
    
    def __repr__(self):
        return '<DxlMotor name={self.name} id={self.id} pos={self.position}>'.format(self=self)

    def _make_accessor(name, rw=False):
        return property(fget=lambda self: getitem(self._values, name),
                        fset=(lambda self, value: setitem(self._values, name, value)) if rw else None)
    
    @property
    def id(self):
        return self._id
    
    @property
    def name(self):
        return self._name

    present_speed = _make_accessor('present_speed')
    present_load = _make_accessor('present_load')

    moving_speed = _make_accessor('moving_speed', rw=True)
    torque_limit = _make_accessor('torque_limit', rw=True)

    pid = _make_accessor('pid', rw=True)

    present_voltage = _make_accessor('present_voltage')
    present_temperature = _make_accessor('present_temperature')
    
    
    @property
    def present_position(self):
        pos = self._values['present_position']
        return (pos if self.direct else -pos) - self.offset
    
    @property
    def goal_position(self):
        pos = self._values['goal_position']
        return (pos if self.direct else -pos) - self.offset
    
    @goal_position.setter
    def goal_position(self, value):
        value = (value + self.offset) if self.direct else -(value + self.offset)
        self._values['goal_position'] = value

    @property
    def position(self):
        return self.present_position

    @position.setter
    def position(self, value):
        self.goal_position = value

    @property
    def compliant(self):
        return self._compliant

    @compliant.setter
    def compliant(self, value):
        self.goal_position = self.present_position
        self._compliant = value

    @property
    def direct(self):
        return self._direct

    @property
    def offset(self):
        return self._offset

    def goto_position(self, position, duration, wait=False):
        dp = abs(self.present_position - position)
        speed = (dp / float(duration)) if duration > 0 else numpy.inf
        
        self.moving_speed = speed
        self.goal_position = position

        if wait:
            time.sleep(duration)


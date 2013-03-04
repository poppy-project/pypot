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
        self._values['compliant'] = True
    
    def __repr__(self):
        return '<DxlMotor name={self.name} id={self.id} pos={self.present_position}>'.format(self=self)

    @classmethod
    def _make_accessor(cls, name, rw=False):
        return property(fget=lambda self: getitem(self._values, name),
                        fset=(lambda self, value: setitem(self._values, name, value)) if rw else None)
    
    @property
    def id(self):
        return self._id
    
    @property
    def name(self):
        return self._name

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
    def present_speed(self):
        speed = self._values['present_speed']
        return (speed if self.direct else -speed)
    
    @property
    def present_load(self):
        load = self._values['present_load']
        return (load if self.direct else -load)

    @property
    def compliant(self):
        return bool(self._values['compliant'])

    @compliant.setter
    def compliant(self, value):
        # Change the goal_position only if you switch from compliant to not compliant mode
        if not value and self.compliant:
            self.goal_position = self.present_position
        self._values['compliant'] = value

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

    
DxlMotor.moving_speed = DxlMotor._make_accessor('moving_speed', rw=True)
DxlMotor.torque_limit = DxlMotor._make_accessor('torque_limit', rw=True)
    
DxlMotor.present_voltage = DxlMotor._make_accessor('present_voltage')
DxlMotor.present_temperature = DxlMotor._make_accessor('present_temperature')


class DxlAXRXMotor(DxlMotor):
    def __init__(self, id, name=None,
                 direct=True, offset=0.0):
        DxlMotor.__init__(self, id, name, direct, offset)
        self.max_pos = 150


DxlAXRXMotor.compliance_margin = DxlAXRXMotor._make_accessor('compliance_margin', rw=True)
DxlAXRXMotor.compliance_slope = DxlAXRXMotor._make_accessor('compliance_slope', rw=True)


class DxlMXMotor(DxlMotor):
    def __init__(self, id, name=None,
                 direct=True, offset=0.0):
        DxlMotor.__init__(self, id, name, direct, offset)
        self.max_pos = 180

DxlMXMotor.pid = DxlMXMotor._make_accessor('pid', rw=True)

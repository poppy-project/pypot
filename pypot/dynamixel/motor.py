# -*- coding: utf-8 -*

import sys
import time
import numpy
import logging

from collections import defaultdict
from operator import getitem, setitem


logger = logging.getLogger(__name__)


class DxlMotor(object):
    """ High-level class used to represent and control a generic dynamixel motor.

        This class provides all level access to:
            * motor id
            * motor name
            * position/speed/load (read and write)
            * compliant
            * motor orientation and offset
            * angle limit
            * temperature
            * voltage

        This class represents a generic robotis motor and you define your own subclass for specific motors (see :class:`~pypot.dynamixel.motor.DxlMXMotor` or :class:`~pypot.dynamixel.motor.DxlAXRXMotor`).

        Those properties are synchronized with the real motors values thanks to a :class:`~pypot.dynamixel.controller.DxlController`.

        """
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

    @property
    def json(self):
        return self.name

    def _setter(self, name, value):
        setitem(self._values, name, value)
        logger.debug("Setting '%s.%s' to %s",
                     self.name, name, value)

    @classmethod
    def _make_accessor(cls, name, rw=False, doc=None):
        def getter(self):
            return getitem(self._values, name)

        def setter(self, value):
            self._setter(name, value)

        return property(fget=getter,
                        fset=setter if rw else None,
                        doc=doc)

    @property
    def id(self):
        """ Id of the motor (readonly). """
        return self._id

    @property
    def name(self):
        """ Name of the motor (readonly). """
        return self._name

    @property
    def present_position(self):
        """ Present position (in degrees) of the motor (readonly). """
        pos = self._values['present_position']
        return (pos if self.direct else -pos) - self.offset

    @property
    def goal_position(self):
        """ Goal position (in degrees) of th motor. """
        pos = self._values['goal_position']
        return (pos if self.direct else -pos) - self.offset

    @goal_position.setter
    def goal_position(self, value):
        framed_value = (value + self.offset) if self.direct else -(value + self.offset)
        self._values['goal_position'] = framed_value

        logger.debug("Setting '%s.goal_position' to %s (%s)",
                     self.name, value, framed_value)

    @property
    def present_speed(self):
        """ Present speed (in degrees per second) of the motor (readonly). """
        speed = self._values['present_speed']
        return (speed if self.direct else -speed)

    @property
    def goal_speed(self):
        """ Goal speed (in degrees per second) of the motor.

            This property can be used to control your motor in speed. Setting a goal speed will automatically change the moving speed and sets the goal position as the angle limit.

            .. note:: The motor will turn until reaching the angle limit. But this is not a wheel mode, so the motor will stop at its limits.

            """
        return numpy.sign(self.goal_position) * self.moving_speed

    @goal_speed.setter
    def goal_speed(self, value):
        if abs(value) < sys.float_info.epsilon:
            self.goal_position = self.present_position

        else:
            # 0.7 corresponds approx. to the min speed that will be converted into 0
            # and as 0 corredsponds to setting the max speed, we have to check this case
            value = numpy.sign(value) * 0.7 if abs(value) < 0.7 else value

            self.goal_position = numpy.sign(value) * self.max_pos
            self.moving_speed = abs(value)

    @property
    def present_load(self):
        """ Present load (in percentage of max load) of the motor (readonly). """
        load = self._values['present_load']
        return (load if self.direct else -load)

    @property
    def compliant(self):
        """ Compliancy of the motor. """
        return bool(self._values['compliant'])

    @compliant.setter
    def compliant(self, value):
        # Change the goal_position only if you switch from compliant to not compliant mode
        if not value and self.compliant:
            self.goal_position = self.present_position
        self._setter('compliant', value)

    @property
    def direct(self):
        """ Orientation of the motor. """
        return self._direct

    @property
    def offset(self):
        """ Offset of the zero of the motor (in degrees). """
        return self._offset

    @property
    def registers(self):
        return [r for r in dir(self) if not r.startswith('_')]

    def goto_position(self, position, duration, wait=False):
        """ Automatically sets the goal position and the moving speed to reach the desired position within the duration. """
        dp = abs(self.present_position - position)
        speed = (dp / float(duration)) if duration > 0 else numpy.inf

        self.moving_speed = speed
        self.goal_position = position

        if wait:
            time.sleep(duration)


DxlMotor.moving_speed = DxlMotor._make_accessor('moving_speed', rw=True,
                                                doc='Moving speed (in degrees per second) of the motor.')
DxlMotor.torque_limit = DxlMotor._make_accessor('torque_limit', rw=True,
                                                doc='Torque limit (in percentage of max torque) of the motor.')

DxlMotor.angle_limit = DxlMotor._make_accessor('angle_limit',
                                               doc='Angle limit (in degrees) of the motor.')
DxlMotor.present_voltage = DxlMotor._make_accessor('present_voltage',
                                                   doc='Present voltage (in V) of the motor.')
DxlMotor.present_temperature = DxlMotor._make_accessor('present_temperature',
                                                       doc='Present temperature (in °C) of the motor.')


class DxlAXRXMotor(DxlMotor):
    """ This class represents the AX robotis motor.

        This class adds access to:
            * compliance margin/slope (see the robotis website for details)

        """
    def __init__(self, id, name=None,
                 direct=True, offset=0.0):
        DxlMotor.__init__(self, id, name, direct, offset)
        self.max_pos = 150


DxlAXRXMotor.compliance_margin = DxlAXRXMotor._make_accessor('compliance_margin', rw=True,
                                                             doc='Compliance margin of the motor (see robotis website).')
DxlAXRXMotor.compliance_slope = DxlAXRXMotor._make_accessor('compliance_slope', rw=True,
                                                            doc='Compliance slope of the motor (see robotis website).')


class DxlMXMotor(DxlMotor):
    def __init__(self, id, name=None,
                 direct=True, offset=0.0):
        """ This class represents the RX and MX robotis motor.

            This class adds access to:
                * PID gains (see the robotis website for details)

            """
        DxlMotor.__init__(self, id, name, direct, offset)
        self.max_pos = 180

DxlMXMotor.pid = DxlMXMotor._make_accessor('pid', rw=True,
                                           doc='PID gains of the motors (see robotis website).')

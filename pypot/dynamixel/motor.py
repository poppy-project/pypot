import numpy
import logging

import pypot.utils.pypot_time as time

from ..robot.motor import Motor

logger = logging.getLogger(__name__)


class DxlRegister(object):
    def __init__(self, rw=False):
        self.rw = rw

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.label, 0)

    def __set__(self, instance, value):
        if not self.rw:
            raise AttributeError("can't set attribute")

        logger.debug("Setting '%s.%s' to %s",
                     instance.name, self.label, value)
        instance.__dict__[self.label] = value


class DxlOrientedRegister(DxlRegister):
    def __get__(self, instance, owner):
        value = DxlRegister.__get__(self, instance, owner)
        return (value if instance.direct else -value)

    def __set__(self, instance, value):
        value = value if instance.direct else -value
        DxlRegister.__set__(self, instance, value)


class DxlPositionRegister(DxlOrientedRegister):
    def __get__(self, instance, owner):
        value = DxlOrientedRegister.__get__(self, instance, owner)
        return value - instance.offset

    def __set__(self, instance, value):
        value = value + instance.offset
        DxlOrientedRegister.__set__(self, instance, value)


class RegisterOwner(type):
    def __new__(cls, name, bases, attrs):
        for n, v in attrs.items():
            if isinstance(v, DxlRegister):
                v.label = n
                attrs['registers'].append(n)
        return super(RegisterOwner, cls).__new__(cls, name, bases, attrs)


class DxlMotor(Motor):
    """ High-level class used to represent and control a generic dynamixel motor.

        This class provides all level access to (see :attr:`~pypot.dynamixel.motor.DxlMotor.registers` for an exhaustive list):
            * motor id
            * motor name
            * motor model
            * present position/speed/load
            * goal position/speed/load
            * compliant
            * motor orientation and offset
            * angle limit
            * temperature
            * voltage

        This class represents a generic robotis motor and you define your own subclass for specific motors (see :class:`~pypot.dynamixel.motor.DxlMXMotor` or :class:`~pypot.dynamixel.motor.DxlAXRXMotor`).

        Those properties are synchronized with the real motors values thanks to a :class:`~pypot.dynamixel.controller.DxlController`.

        """
    __metaclass__ = RegisterOwner

    registers = ['registers', 'goal_speed', 'compliant']

    id = DxlRegister()
    name = DxlRegister()
    model = DxlRegister()

    present_position = DxlPositionRegister()
    goal_position = DxlPositionRegister(rw=True)
    present_speed = DxlOrientedRegister()
    moving_speed = DxlRegister(rw=True)
    present_load = DxlOrientedRegister()
    torque_limit = DxlRegister(rw=True)

    angle_limit = DxlRegister()
    present_voltage = DxlRegister()
    present_temperature = DxlRegister()

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0):
        self.__dict__['id'] = id

        name = name if name is not None else 'motor_{}'.format(id)
        self.__dict__['name'] = name

        self.__dict__['model'] = model
        self.__dict__['direct'] = direct
        self.__dict__['offset'] = offset

        self.__dict__['compliant'] = True

    def __repr__(self):
        return ('<DxlMotor name={self.name} '
                'id={self.id} '
                'pos={self.present_position}>').format(self=self)

    @property
    def json(self):
        return self.name

    @property
    def goal_speed(self):
        """ Goal speed (in degrees per second) of the motor.

            This property can be used to control your motor in speed. Setting a goal speed will automatically change the moving speed and sets the goal position as the angle limit.

            .. note:: The motor will turn until reaching the angle limit. But this is not a wheel mode, so the motor will stop at its limits.

            """
        return numpy.sign(self.goal_position) * self.moving_speed

    @goal_speed.setter
    def goal_speed(self, value):
        if abs(value) < numpy.finfo(numpy.float).eps:
            self.goal_position = self.present_position

        else:
            # 0.7 corresponds approx. to the min speed that will be converted into 0
            # and as 0 corredsponds to setting the max speed, we have to check this case
            value = numpy.sign(value) * 0.7 if abs(value) < 0.7 else value

            self.goal_position = numpy.sign(value) * self.max_pos
            self.moving_speed = abs(value)

    @property
    def compliant(self):
        return bool(self.__dict__['compliant'])

    @compliant.setter
    def compliant(self, value):
        # Change the goal_position only if you switch from compliant to not compliant mode
        if not value and self.compliant:
            self.goal_position = self.present_position
        self.__dict__['compliant'] = value

    def goto_position(self, position, duration, wait=False):
        """ Automatically sets the goal position and the moving speed to reach the desired position within the duration. """
        dp = abs(self.present_position - position)
        speed = (dp / float(duration)) if duration > 0 else numpy.inf

        self.moving_speed = speed
        self.goal_position = position

        if wait:
            time.sleep(duration)


class DxlAXRXMotor(DxlMotor):
    """ This class represents the AX robotis motor.

        This class adds access to:
            * compliance margin/slope (see the robotis website for details)

        """
    registers = list(DxlMotor.registers)

    compliance_margin = DxlRegister(rw=True)
    compliance_slope = DxlRegister(rw=True)

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0):
        DxlMotor.__init__(self, id, name, model, direct, offset)
        self.max_pos = 150


class DxlMXMotor(DxlMotor):
    registers = list(DxlMotor.registers)

    pid = DxlRegister(rw=True)

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0):
        """ This class represents the RX and MX robotis motor.

            This class adds access to:
                * PID gains (see the robotis website for details)

            """
        DxlMotor.__init__(self, id, name, model, direct, offset)
        self.max_pos = 180

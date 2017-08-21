import numpy
import logging

from collections import defaultdict

import pypot.utils.pypot_time as time

from ..robot.motor import Motor

from ..utils import SyncEvent
from ..utils.trajectory import GotoMinJerk
from ..utils.stoppablethread import StoppableLoopThread


logger = logging.getLogger(__name__)


class DxlRegister(object):
    def __init__(self, rw=False):
        self.rw = rw

    def __get__(self, instance, owner):
        if instance._read_synchronous[self.label]:
            sync = instance._read_synced[self.label]

            if not sync.is_recent:
                sync.request()

        value = instance.__dict__.get(self.label, 0)

        return value

    def __set__(self, instance, value):
        if not self.rw:
            raise AttributeError("can't set attribute")

        logger.debug("Setting '%s.%s' to %s",
                     instance.name, self.label, value)
        instance.__dict__[self.label] = value

        if instance._write_synchronous[self.label]:
            sync = instance._write_synced[self.label]
            sync.request()


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

    registers = Motor.registers + ['registers',
                                   'goal_speed',
                                   'compliant', 'safe_compliant',
                                   'angle_limit']

    id = DxlRegister()
    name = DxlRegister()
    model = DxlRegister()

    present_position = DxlPositionRegister()
    goal_position = DxlPositionRegister(rw=True)
    present_speed = DxlOrientedRegister()
    moving_speed = DxlOrientedRegister(rw=True)
    present_load = DxlOrientedRegister()
    torque_limit = DxlRegister(rw=True)

    lower_limit = DxlPositionRegister()
    upper_limit = DxlPositionRegister()
    present_voltage = DxlRegister()
    present_temperature = DxlRegister()

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0,
                 broken=False,
                 angle_limit=None):
        self.__dict__['id'] = id

        name = name if name is not None else 'motor_{}'.format(id)
        self.__dict__['name'] = name

        self.__dict__['model'] = model
        self.__dict__['direct'] = direct
        self.__dict__['offset'] = offset

        self.__dict__['compliant'] = True

        self._safe_compliance = SafeCompliance(self)
        self.goto_behavior = 'dummy'
        self.compliant_behavior = 'dummy'

        self._broken = broken

        self._read_synchronous = defaultdict(lambda: False)
        self._read_synced = defaultdict(SyncEvent)

        self._write_synchronous = defaultdict(lambda: False)
        self._write_synced = defaultdict(SyncEvent)

        if angle_limit is not None:
            self.__dict__['lower_limit'], self.__dict__['upper_limit'] = angle_limit

    def __repr__(self):
        return ('<DxlMotor name={self.name} '
                'id={self.id} '
                'pos={self.present_position}>').format(self=self)

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
    def compliant_behavior(self):
        return self._compliant_behavior

    @compliant_behavior.setter
    def compliant_behavior(self, value):
        if value not in ('dummy', 'safe'):
            raise ValueError('Wrong compliant type! It should be either "dummy" or "safe".')

        if hasattr(self, '_compliant_behavior') and self._compliant_behavior == value:
            return

        self._compliant_behavior = value

        # Start the safe compliance behavior when the motor should be compliant
        if value is 'safe' and self.compliant:
            self._safe_compliance.start()

        if value is 'dummy':
            use_safe = self._safe_compliance.started
            if use_safe:
                self._safe_compliance.stop()
            self.compliant = self.compliant or use_safe

    @property
    def compliant(self):
        return bool(self.__dict__['compliant'])

    @compliant.setter
    def compliant(self, is_compliant):
        if self._safe_compliance.started and is_compliant:
            return

        if self.compliant_behavior == 'dummy':
            self._set_compliancy(is_compliant)

        elif self.compliant_behavior == 'safe':
            if is_compliant:
                self._safe_compliance.start()
            elif self._safe_compliance.started:
                self._safe_compliance.stop()

    def _set_compliancy(self, is_compliant):
        # Change the goal_position only if you switch from compliant to not compliant mode
        if not is_compliant and self.compliant:
            self.goal_position = self.present_position
        self.__dict__['compliant'] = is_compliant

    @property
    def angle_limit(self):
        return self.lower_limit, self.upper_limit

    @angle_limit.setter
    def angle_limit(self, limits):
        self.lower_limit, self.upper_limit = limits

    @property
    def goto_behavior(self):
        return self._default_goto_behavior

    @goto_behavior.setter
    def goto_behavior(self, value):
        if value not in ('dummy', 'minjerk'):
            raise ValueError('Wrong compliant type! It should be either "dummy" or "minjerk".')
        self._default_goto_behavior = value

    def goto_position(self, position, duration, control=None, wait=False):
        """ Automatically sets the goal position and the moving speed to reach the desired position within the duration. """

        if control is None:
            control = self.goto_behavior

        if control == 'minjerk':
            goto_min_jerk = GotoMinJerk(self, position, duration)
            goto_min_jerk.start()

            if wait:
                goto_min_jerk.wait_to_stop()

        elif control == 'dummy':
            dp = abs(self.present_position - position)
            speed = (dp / float(duration)) if duration > 0 else 0

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
                 direct=True, offset=0.0, broken=False,
                 angle_limit=None):
        DxlMotor.__init__(self, id, name, model,
                          direct, offset, broken,
                          angle_limit)
        self.max_pos = 150


class DxlMXMotor(DxlMotor):
    """ This class represents the RX and MX robotis motor.

        This class adds access to:
            * PID gains (see the robotis website for details)

        """
    registers = list(DxlMotor.registers)

    pid = DxlRegister(rw=True)

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0, broken=False,
                 angle_limit=None):
        """ This class represents the RX and MX robotis motor.

            This class adds access to:
                * PID gains (see the robotis website for details)

            """
        DxlMotor.__init__(self, id, name, model,
                          direct, offset, broken,
                          angle_limit)
        self.max_pos = 180


class DxlMX64106Motor(DxlMXMotor):
    """ This class represents the MX-64 and MX-106 robotis motor.

        This class adds access to:
            * present current

        """

    registers = list(DxlMXMotor.registers)

    present_current = DxlRegister()

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0, broken=False,
                 angle_limit=None):
        """ This class represents the RX and MX robotis motor.

            This class adds access to:
                * PID gains (see the robotis website for details)

            """
        DxlMotor.__init__(self, id, name, model,
                          direct, offset, broken,
                          angle_limit)
        self.max_pos = 180


class DxlXL320Motor(DxlMXMotor):
    registers = list(DxlMXMotor.registers)

    led = DxlRegister(rw=True)
    control_mode = DxlRegister(rw=True)

    """ This class represents the XL-320 robotis motor. """
    def __init__(self, id, name=None, model='XL-320',
                 direct=True, offset=0.0, broken=False,
                 angle_limit=None):
        DxlMXMotor.__init__(self, id, name, model,
                            direct, offset, broken,
                            angle_limit)
        self.max_pos = 150


class DxlSRMotor(DxlMotor):
    """ This class represents the robotis motor found in the seed robotics hand.

        This class adds access to:
            * force control enable
            * goal force
            * present current

        """
    registers = list(DxlMotor.registers)

    force_control_enable = DxlRegister(rw=True)
    goal_force = DxlRegister(rw=True)
    present_current = DxlRegister()

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0, broken=False,
                 angle_limit=None):
        """ This class represents the robotis motor found in the seed robotics hand.

        This class adds access to:
            * PID gains (see the robotis website for details)
            * force control enable
            * goal force

            """
        DxlMotor.__init__(self, id, name, model,
                          direct, offset, broken,
                          angle_limit)
        self.max_pos = 180


class SafeCompliance(StoppableLoopThread):
    """ This class creates a controller to active compliance only if the current motor position is included in the angle limit, else the compliance is turned off. """

    def __init__(self, motor, frequency=50):
        StoppableLoopThread.__init__(self, frequency)

        self.motor = motor

    def update(self):
        self.motor._set_compliancy((min(self.motor.angle_limit) < self.motor.present_position < max(self.motor.angle_limit)))

    def teardown(self):
        self.motor._set_compliancy(False)

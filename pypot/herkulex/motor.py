import numpy
import logging

import pypot.utils.pypot_time as time
from pypot.robot.motor import Motor
from pypot.utils.trajectory import GotoMinJerk
from pypot.utils.stoppablethread import StoppableLoopThread

from conversion import hkx_max_playtime
from conversion import hkx_max_speed

logger = logging.getLogger(__name__)


class HkxRegister(object):
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


class HkxOrientedRegister(HkxRegister):
    def __get__(self, instance, owner):
        value = HkxRegister.__get__(self, instance, owner)
        return (value if instance.direct else -value)

    def __set__(self, instance, value):
        value = value if instance.direct else -value
        HkxRegister.__set__(self, instance, value)


class HkxPositionRegister(HkxOrientedRegister):
    def __get__(self, instance, owner):
        value = HkxOrientedRegister.__get__(self, instance, owner)
        return value - instance.offset

    def __set__(self, instance, value):
        value = value + instance.offset
        HkxOrientedRegister.__set__(self, instance, value)


class RegisterOwner(type):
    def __new__(cls, name, bases, attrs):
        for n, v in attrs.items():
            if isinstance(v, HkxRegister):
                v.label = n
                attrs['registers'].append(n)
        return super(RegisterOwner, cls).__new__(cls, name, bases, attrs)


class HkxMotor(Motor):
    """ High-level class used to represent and control a generic herkulex motor.

        This class provides all level access to (see :attr:`~pypot.herkulex.motor.HkxMotor.registers` for an exhaustive list):
            * motor id
            * motor name
            * motor model
            * present position/speed/load
            * new goal position / execution time for one-shot jog instruction
            * torque limit
            * compliant
            * motor orientation and offset
            * angle limit
            * temperature
            * voltage

        This class represents a generic herkulex motor and you define your own subclass for specific motors.

        Those properties are synchronized with the real motors values thanks to a :class:`~pypot.herkulex.controller.HkxController`.

        """
    __metaclass__ = RegisterOwner

    registers = Motor.registers + ['registers',
                                   'goal_speed',
                                   'compliant', 'safe_compliant',
                                   'angle_limit']

    id = HkxRegister()
    name = HkxRegister()
    model = HkxRegister()

    present_position = HkxPositionRegister() 
    _goal_position_register = HkxPositionRegister()#read only, the write part is done with _goal_position
    present_speed = HkxOrientedRegister()
    present_load = HkxOrientedRegister()
    torque_limit = HkxRegister(rw=True)

    lower_limit = HkxPositionRegister()
    upper_limit = HkxPositionRegister()
    present_voltage = HkxRegister()
    present_temperature = HkxRegister()

    def __init__(self, id, name=None, model='',
                 direct=True, offset=0.0,
                 broken=False):
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
        self._exec_time = -1.
        self._goal_position = 0. #used to set goal position (RO register, only changed via jog)
        self._moving_speed = -1. #simulate a target speed register

    def __repr__(self):
        return ('<HkxMotor name={self.name} '
                'id={self.id} '
                'pos={self.present_position}>').format(self=self)

          
##################TODO: add speed control
 
    @property
    def moving_speed(self):
        return self._moving_speed

    @moving_speed.setter
    def moving_speed(self, ns):
        self._moving_speed = min(ns, hkx_max_speed)
        #setting speed to 0 means max speed (to mimick Dxl)
        if ns == 0:
            self._moving_speed = hkx_max_speed
        #if we are not at goal position, try to reach it
        if not self._goal_position == self.present_position:
            self._enforce_speed_logic()
        else:
            self._exec_time = -1
            
    @property
    def goal_position(self):
        return self._goal_position

    @goal_position.setter
    def goal_position(self, gpos):
        self._goal_position = gpos
        #if we have nonzero moving speed, go to the new goal position
        if self.moving_speed > 0:
            self._enforce_speed_logic()
        else:
            self._exec_time = -1

    #make sure we don't exceed the max playtime when moves triggered by goal position / goal speed changes
    #this is done by adjusting the moving speed
    #TODO: improve by splitting the move accross several update cycles instead?
    def _enforce_speed_logic(self):
        theoexec = abs(self._goal_position - self.present_position) / self.moving_speed
        if theoexec <= hkx_max_playtime:
            self._exec_time = theoexec
        else:
            self._exec_time = hkx_max_playtime
            self._moving_speed = (self._goal_position - self.present_position) / hkx_max_playtime
      
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
        #TODO: check if we need to keep the below test as well for hkx (i.e. jog to current position when switching from compliant to non-compliant)
        # Change the goal_position only if you switch from compliant to not compliant mode
        #if not is_compliant and self.compliant:
        #    self.goal_position = self.present_position
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
        """ Reach the desired position within the specified duration"""
        #make sure we don't exceed the max playtime
        #this is done by adjusting the duration
        #TODO: improve by splitting the move accross several update cycles instead?
        duration = min(duration, hkx_max_playtime)
        #also keep track of the implied moving speed
        #if the implied speed is 0, we do NOT transform it to the maximum speed
        self._moving_speed = abs(position - self.present_position) / (duration)
        if control is None:
            control = self.goto_behavior
        #TODO: investigate minjerk through the min PWM register?
        if control == 'minjerk':
            pass
        elif control == 'dummy':
            self._exec_time = duration
            self.goal_position = position

            if wait:
                time.sleep(duration)

class SafeCompliance(StoppableLoopThread):
    """ This class creates a controller to active compliance only if the current motor position is included in the angle limit, else the compliance is turned off. """

    def __init__(self, motor, frequency=50):
        StoppableLoopThread.__init__(self, frequency)
        self.motor = motor

    def update(self):
        self.motor._set_compliancy((min(self.motor.angle_limit) < self.motor.present_position < max(self.motor.angle_limit)))

    def teardown(self):
        self.motor._set_compliancy(False)

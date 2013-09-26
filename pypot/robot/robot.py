import time

import pypot.robot.xmlparser
import pypot.primitive.manager
import pypot.dynamixel.controller


class Robot(object):
    """
        This class is used to regroup all motors (and soon sensors) of your robots.
        
        Most of the time, you do not want to directly instantiate this class, 
        but you rather want to use the factory which creates a robot instance 
        from a configuration file, currently a xml file (see :ref:`config_file`).
        
        This class encapsulates the different controllers (such as dynamixel ones)
        that automatically synchronize the virtual sensors/effectors instances held
        by the robot class with the real devices. By doing so, each sensor/efector 
        can be synchronized at a different frequency.
        
        This class also provides a generic motors accessor in order to (more or less)
        easily extends this class to other types of motor.
        
        """
    def __init__(self):
        self._motors = []
        self.alias = []
        self._attached_primitives = {}
        self._dxl_controllers = []
        self._primitive_manager = pypot.primitive.manager.PrimitiveManager(self.motors)
    
    def __repr__(self):
        return '<Robot motors={}>'.format(self.motors)

    def _attach_dxl_motors(self, dxl_io, dxl_motors):
        c = pypot.dynamixel.controller.BaseDxlController(dxl_io, dxl_motors)
        self._dxl_controllers.append(c)
        
        for m in dxl_motors:
            setattr(self, m.name, m)
        
        self._motors.extend(dxl_motors)

    def start_sync(self):
        """ Starts all the synchonization loop (sensor/effector controllers). """
        self._primitive_manager.start()
        map(lambda c: c.start(), self._dxl_controllers)

    def stop_sync(self):
        """ Stops all the synchonization loop (sensor/effector controllers). """
        self._primitive_manager.stop()
        map(lambda c: c.stop(), self._dxl_controllers)
    
    def attach_primitive(self, primitive, name):
        setattr(self, name, primitive)
        self._attached_primitives[name] = primitive

    def attach_move(self, move, name):
        move_player = pypot.robot.MovePlayer(self, move)
        setattr(self, name, move_player)

    @property
    def motors(self):
        """ Returns all the motors attached to the robot. """
        return self._motors
    
    @property
    def primitives(self):
        """ Returns all the primitives attached to the robot. """
        return self._attached_primitives.values()
    
    @property
    def primitives_name(self):
        """ Returns all the primitives name attached to the robot. """
        return self._attached_primitives.keys()

    @property
    def compliant(self):
        """ Returns a list of all the compliant motors. """
        return filter(lambda m: m.compliant, self.motors)

    @compliant.setter
    def compliant(self, is_compliant):
        """ Switches all motors to compliant (resp. non compliant) mode. """
        for m in self.motors:
            m.compliant = is_compliant

    def goto_position(self, position_for_motors, duration, wait=False):
        """ Moves a subset of the motors to a position within a specific duration.
            
            :param dict position_for_motors: which motors you want to move {motor_name: pos, motor_name: pos,...}
            :param float duration: duration of the move
            :param bool wait: whether or not to wait for the end of the move
            
            .. note::In case of dynamixel motors, the speed is automatically adjusted so the goal position is reached after the chosen duration.
            
            """
        for motor_name, position in position_for_motors.iteritems():
            m = getattr(self, motor_name)
            m.goto_position(position, duration)

        if wait:
            time.sleep(duration)

    def power_up(self):
        """ Changes all settings to guarantee the motors will be used at their maximum power. """
        for m in self.motors:
            m.compliant = False
            m.moving_speed = 0
            m.torque_limit = 100.0


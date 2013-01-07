import pypot.robot.xmlparser
import pypot.primitive.manager
import pypot.dynamixel.controller

class Robot(object):
    def __init__(self):
        self._motors = []
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
        self._primitive_manager.start()
        map(lambda c: c.start(), self._dxl_controllers)

    def stop_sync(self):
        self._primitive_manager.stop()
        map(lambda c: c.stop(), self._dxl_controllers)
    
    def attach_primitive(self, primitive, name):
        setattr(self, name, primitive)

    @property
    def motors(self):
        """ Returs all the motors attached to the robot. """
        return self._motors

    def goto_position(self, position_for_motors, duration):
        for motor_name, position in position_for_motors.iteritems():
            m = getattr(self, motor_name)
            dp = abs(m.present_position - position)
            speed = dp / float(duration)

            m.moving_speed = speed
            m.goal_position = position

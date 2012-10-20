import pypot.config.xmlparser

class Robot(object):
    """ 
        High level access to motors.
        
        Robot is a set of configured motors that are controllable through a 
        :py:class:`~pypot.DynamixelController`.
        The motors can be accessed as an attribute of the Robot 
        (see :py:meth:`__getattr__` for more information).
        
        :param string name: Name of the Robot
        
        :param motors: List of motors on the Robot.
        :type motors: list of :py:class:`~pypot.dynamixel.DynamixelMotor`
        
        :param controllers: Bus controller for motors.
        :type controllers: list of :py:class:`~pypot.dynamixel.DynamixelController`
        
        .. note:: The motors are automatically configured during the initialization:
        i.e. we check their eeprom to match the eeprom configuration file used.
        
        .. note:: the read/write cycle of motors is automatically
            triggered on initialization.
        
        """
    def __init__(self, name, motors, controllers, eeprom_values):
        self.name = name
        self.motors = motors
        self.controllers = controllers
        
        #for m in self.motors:
        #    class Holder:
        #        p = property(lambda x: self.motors[m])
        #    setattr(self, m, Holder().p)
        
        # TODO: add properties corr. to motors name
        # To add them only to the current instance and not the class
        # We use the following trick
        #   class Holder:
        #       p = property(lambda x: vs[i])
        #   setattr(self, 'p', Holder().p)
    
        # [c.configure_motors(eeprom_values) for c in self.controllers]

    
    @classmethod
    def from_configuration(cls, configuration_file):
        """ 
            Creates a robot from the configuration file.
            
            Creates a robot initialized with the controllers, motors specified
            in the xml file.
            
            """
        return pypot.config.xmlparser.load_robot_configuration(configuration_file)
    
    def __repr__(self):
        return '<Robot name=%s motors=%s>' % (self.name, ''.join(map(repr, self.motors)))
    
    
    def __getattr__(self, name):
        """ Finds the motor given its name. """
        try:
            return filter(lambda m: m.name == name, self.motors)[0]
        
        except IndexError:
            return object.__getattr__(self, name)


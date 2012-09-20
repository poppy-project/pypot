

class DynamixelMotor(object):
    """ Creates access to the possible values that can be read from/written to the motors.
        
        :param kwargs: You can specify custom eeprom values via keyword argument.
        The keyword must match the name used in the getter/setter of the DynamixelIO
        class (e.g. 'angle_limits', 'return_delay_time').
        
        """
    def __init__(self,
                 id, name, model, is_direct=True,
                 io=None,
                 **kwargs):
        
        self.id = id
        self.name = name
        self.model = model
        self.direct = is_direct
        
        self.io = io
        self._current_position = self._goal_position = 0
        
        self.synced = True
        self._compliant = False
        
        self.custom_eeprom_values = kwargs
        
    def __repr__(self):
        return '<Motor name=%s id=%d model=%s pos=%g>' % (self.name,
                                                          self.id,
                                                          self.model,
                                                          self.current_position)
    
    @property
    def current_position(self):
        return self._current_position if self.direct else -self._current_position
    
    @property
    def goal_position(self):
        return self._goal_position if self.direct else -self._goal_position
    
    @goal_position.setter
    def goal_position(self, value):
        self._goal_position = value if self.direct else -value
    
    
        
    @property
    def compliant(self):
        return self._compliant

    @compliant.setter
    def compliant(self, value):
        self._compliant = value
        
        if value:
            self.io.disable_torque(self.id)
            self.synced = False
        else:
            self.goal_position = self.current_position
            self.io.enable_torque(self.id)
            self.synced = True
        
            



class _DynamixelMotor(object):
    @classmethod
    def _generate_accessor(cls, varname, readonly):
        prefix = '__sync_read_' if readonly else '__sync_write_'
        
        def lazy_getter(self, varname):
            lazy_varname = prefix + varname
    
            if hasattr(self, lazy_varname):
                return getattr(self, lazy_varname)

            else:
                return getattr(self._io, 'get_' + varname)(self.id)

        def lazy_setter(self, varname, value):
            lazy_varname = prefix + varname
                
            if hasattr(self, lazy_varname):
                setattr(self, lazy_varname, value)
                
            else:
                getattr(self._io, 'set_' + varname)(self.id, value)

        getter = lambda self: lazy_getter(self, varname)
        setter = lambda self, value: lazy_setter(self, varname, value)

        if readonly:
            setattr(cls, varname, property(getter))
        else:
            setattr(cls, varname, property(getter, setter))
            
            
    @classmethod
    def _generate_read_accessor(cls, varname):
        cls._generate_accessor(varname, True)
    
    @classmethod
    def _generate_write_accessor(cls, varname):
        cls._generate_accessor(varname, False)



class DynamixelMotor(_DynamixelMotor):
    """ Creates access to the possible values that can be read from/written to the motors.
        
        :param kwargs: You can specify custom eeprom values via keyword argument.
        The keyword must match the name used in the getter/setter of the DynamixelIO
        class (e.g. 'angle_limits', 'return_delay_time').
        
        """
    def __init__(self,
                 id, name, model,
                 is_direct=True, offset=0.0,
                 io=None,
                 **kwargs):
        
        self.id = id
        self.name = name
        self.model = model
        self._direct = is_direct
        self._offset = offset

        self._io = io

        self.custom_eeprom_values = kwargs
        
    def __repr__(self):
        return '<Motor name=%s id=%d model=%s pos=%g>' % (self.name,
                                                          self.id,
                                                          self.model,
                                                          self.current_position)
    
    # MARK: - Orientation and offset
    
    @property
    def direct(self):
        return self._direct
    
    @property
    def offset(self):
        return self._offset
    
    
    @property
    def current_position(self):
        pos = _DynamixelMotor.current_position.fget(self)
        return (pos if self.direct else -pos) - self.offset

    @property
    def goal_position(self):
        pos = _DynamixelMotor.goal_position.fget(self)
        return (pos if self.direct else -pos) - self.offset

    @goal_position.setter
    def goal_position(self, value):
        value = (value if self.direct else -value)
        value = value + (self.offset if self.direct else -self.offset)

        _DynamixelMotor.goal_position.fset(self, value)
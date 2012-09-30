import threading
import time

import pypot.dynamixel

class DynamixelController(object):
    """ Creates a bus control system which synchronizes the reading/writing of values of motors. """
    
    TYPE = ("USB2DXL", "USB2AX")
    
    def __init__(self,
                 port, connection_type,
                 motors,
                 blacklisted_alarms=()):
        """
            :param string port: The serial port to control.
            
            :param connection_type: The type of device used.
            :type connection_type: :py:const:`DynamixelController.TYPE`
            
            :param motors: The list of motors on the bus that you want to control.
            :type motors: list of :py:class:`~pypot.dynamixel.DynamixelMotor`
            
            :raises: ValueError if the connection type is unknown.
            
            """                
        if connection_type not in DynamixelController.TYPE:
            raise ValueError('Unknown controller type: %s' % (connection_type))
        
        self.type = connection_type
    
        self.io = pypot.dynamixel.DynamixelIO(port, blacklisted_alarms=blacklisted_alarms)
        self.motors = motors
        for m in self.motors:
            m._io = self.io
            
        self.sync_loops = []
        self.sync_loops.append(DynamixelController._Loop(50,
                                                         self.io, self.motors,
                                                         var_read=('current_position', ),
                                                         var_write=('goal_position', )))

        self.sync_loops.append(DynamixelController._Loop(1,
                                                         self.io, self.motors,
                                                         var_read=('temperature', )))
    
    def __repr__(self):
        return '<Controller io=%s motors=%s>' % (self.io, ''.join([repr(m) for m in self.motors]))
    
    
    # MARK: - Synchronization loops
    
    def start_sync(self):
        """ Starts the synchronization thread. """
        [loop.start() for loop in self.sync_loops]
    
    
    class _Loop(threading.Thread):
        def __init__(self,
                     frequency,
                     io, motors,
                     var_read=(), var_write=()):
            
            threading.Thread.__init__(self)
            self.daemon = True
            
            self.period = 1.0 / frequency
            
            self.motors = motors
        
            self.getters = [(getattr(io, 'get_' + var), '__sync_read_' + var) for var in var_read]
            self.setters = [(getattr(io, 'set_' + var), '__sync_write_' + var) for var in var_write]
      
        
        def run(self):
            # Before running the sync loop,
            # we first get the initial values to avoid "jumping" behavior.
            for _, varname in self.setters:
                for m in self.motors:
                    setattr(m, varname,
                            getattr(pypot.dynamixel._DynamixelMotor, varname.replace('__sync_write_', '')).fget(m))
        
            while True:
                start = time.time()

                for m in self.motors:
                    for getter, varname in self.getters:
                        setattr(m, varname, getter(m.id))
    
                    for setter, varname in self.setters:
                        setter(m.id, getattr(m, varname))
                    
                end = time.time()
            
                elapsed_time = end - start
                sleep_time = self.period - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    
    
    # MARK: - Motor configuration at start
    
    def configure_motors(self, default_eeprom_values):
        """ Sets up the required eeprom values for each of the motors.
            
            Motors can have either default values or custom values for their eeprom. 
            Here both sets of values are written to the eeprom. 
            
            .. note:: If both the default and custom exist, the custom value is used.
            
            :param default_eeprom_values: dictionary of register names and values to be written
            :type default_eeprom_values: dict
            
            """
        [self._configure_motor(m, default_eeprom_values) for m in self.motors]
    
    def _configure_motor(self, motor, default_eeprom_values):
        eeprom = dict(default_eeprom_values)
        eeprom.update(motor.custom_eeprom_values)
        
        if eeprom.has_key('angle_limits'):
            if motor.offset:
                eeprom['angle_limits'] = (eeprom['angle_limits'][0] + motor.offset,
                                          eeprom['angle_limits'][1] + motor.offset)

            if not motor.direct:
                eeprom['angle_limits'] = (-eeprom['angle_limits'][1],
                                          -eeprom['angle_limits'][0])
        
        for key, value in eeprom.items():
            getter = getattr(self.io, 'get_' + key)
            existing_value = getter(motor.id)
        
            if existing_value != value:
                setter = getattr(self.io, 'set_' + key)
           
                if not hasattr(value, '__len__'):
                    value = [value]
                
                args = [motor.id] + list(value)
                setter(*args)
        
                # TODO: check if this behavior exists with all kinds of motors
                # It seems that it is working with AX-12 and not with MX-28.
        
                # We force a sleep here as accessing eeprom values seems to put the
                # motor in a "busy" mode.
                time.sleep(0.5)
    



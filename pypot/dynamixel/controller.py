import threading
import time

import pypot.dynamixel

class DynamixelController(threading.Thread):
    """ Creates a bus control system which synchronizes the reading/writing of values of motors. """
    
    TYPE = ("USB2DXL", "USB2AX")
    
    def __init__(self,
                 port, connection_type, motors,
                 blacklisted_alarms=()):
        """
            :param string port: The serial port to control.
            
            :param connection_type: The type of device used.
            :type connection_type: :py:const:`DynamixelController.TYPE`
            
            :param motors: The list of motors on the bus that you want to control.
            :type motors: list of :py:class:`~pypot.dynamixel.DynamixelMotor`
            
            :raises: ValueError if the connection type is unknown.
            
            """        
        threading.Thread.__init__(self)
        self.daemon = True
        
        if connection_type not in DynamixelController.TYPE:
            raise ValueError('Unknown controller type: %s' % (connection_type))
        
        self.type = connection_type
    
        self.io = pypot.dynamixel.DynamixelIO(port, blacklisted_alarms=blacklisted_alarms)
        self.motors = motors
        for m in self.motors:
            m._io = self.io
        
        [self._get_initial_position_motor(m) for m in self.motors]

    def __repr__(self):
        return '<Controller io=%s motors=%s>' % (self.io, ''.join([repr(m) for m in self.motors]))
    
    
    def _get_initial_position_motor(self, motor):
        """ Retrieves the initial motor position to avoid uncontrolled movement of motors. """
        pos = self.io.get_position(motor.id)
        motor._current_position = motor._goal_position = pos
    
    
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
    

    def start_sync(self):
        """ Starts the synchronization thread. """
        self.start()
    
    
    def run(self):
        """ Sets up the read/write loop. """
        # TODO: v2 possibility of choosing wihch values to sync
        # TODO: v2 choose the refresh frequency (per value ?)
        while True:
            start = time.time()
            
            if self.type == 'USB2AX':
                positions = self.io.get_sync_positions([m.id for m in self.motors])
            
            elif self.type == 'USB2DXL':
                positions = [self.io.get_position(m.id) for m in self.motors]
                
            for (m, p) in zip(self.motors, positions):
                    m._current_position = p

            # TODO: pb si on change la compliance en meme tps qu'on set les pos                        
            self.io.set_sync_positions(map(lambda m: (m.id, m._goal_position),
                                           filter(lambda m: m.synced, self.motors)))
        
            end = time.time()
        
            dt = 0.020 - (end - start)
            if dt > 0:
                time.sleep(dt)

# -*- coding: utf-8 -*-

import threading
import time

import pypot.dynamixel

# TODO:
#class BasicController(DynamixelController):
#def __init__ (sefl...)
#    DynamixelController.__init__
#    self.add_sync_loop(20, var_read = 'position', 'speed', 'load')

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
        
        self.loop_factory = DynamixelController._AXLoop if type == 'USB2AX' else DynamixelController._Loop
    
        self.io = pypot.dynamixel.DynamixelIO(port, blacklisted_alarms=blacklisted_alarms)
        self.motors = motors
        for m in self.motors:
            m._io = self.io
            
        self.sync_loops = []
    

    def __repr__(self):
        return '<Controller io=%s motors=%s>' % (self.io, ''.join([repr(m) for m in self.motors]))
    
    
    # MARK: - Synchronization loops
                
    def add_sync_loop(self, frequency, var_read=(), var_write=()):
        loop = self.loop_factory(frequency,
                                 self.io, self.motors,
                                 var_read=var_read,
                                 var_write=var_write)
                
        loop.start()
        self.sync_loops.append(loop)
            
              
    class _Loop(threading.Thread):
        def __init__(self,
                     frequency,
                     io, motors,
                     var_read=(), var_write=()):
            
            threading.Thread.__init__(self)
            self.daemon = True
            
            self.period = 1.0 / frequency
            
            self.motors = motors
            
            # TODO:
            # si ds var_read/var_write il y a au moins deux éléments parmi (position, speed, load)
            # les remplacer par un seul appel à get_pos_speed_load
            # et set un bool a True
            
            self.getters = [(getattr(io, 'get_' + var), '__sync_read_' + var) for var in var_read]
            self.setters = [(getattr(io, 'set_sync_' + var), '__sync_write_' + var) for var in var_write]
        
        # si on a pos, ou speed ou load ds getters ou setters
        # remplacer les occ par le get/set des trois
        
        def initialize_value(self):
            for _, varname in self.setters:
                for m in self.motors:
                    setattr(m, varname,
                            getattr(pypot.dynamixel._DynamixelMotor,
                                    varname.replace('__sync_write_', '')).fget(m))
    
            for m in self.motors:
                m.compliant = False
        # TODO:
        # ajouter un get special pour pos/speed/load
        # ajouter un set special pour pos/speed/load
        # tester si le bool est True et si non pass
    
        def get(self):
            for m in self.motors:
                for getter, varname in self.getters:
                    setattr(m, varname, getter(m.id))
    
        def set(self):
            motors = filter(lambda m: not m.compliant, self.motors)
            
            if not motors:
                return
            
            for setter, varname in self.setters:
                setter([(m.id, getattr(m, varname)) for m in motors])
        
        def run(self):
            self.initialize_value()
        
            while True:
                start = time.time()
                
                self.get()
                self.set()
                
                end = time.time()
            
                elapsed_time = end - start
                sleep_time = self.period - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    class _AXLoop(_Loop):
        def __init__(self,
                     frequency,
                     io, motors,
                     var_read=(), var_write=()):
            _Loop.__init__(self, frequency, io, motors, var_read, var_write)
    
            self.getters = [(getattr(io, 'get_sync_' + var), '__sync_read_' + var) for var in var_read]


        def get(self):
            for getter, varname in self.getters:
                values = getter([m.id for m in self.motors])

                for m, v in zip(self.motors, values):
                    m.varname = v
    
    
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
    



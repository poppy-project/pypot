# -*- coding: utf-8 -*-

import time
import array
import serial
import operator
import threading

from collections import namedtuple


from pypot.dynamixel.error import BaseErrorHandler
from pypot.dynamixel.conversion import *
from pypot.dynamixel.packet import *


class _DynamixelIO(object):
    """ This class handles the low-level communication with robotis motors.
        
        Using a USB communication device such as USB2DYNAMIXEL or USB2AX,
        you can open serial communication with robotis motors (MX, RX, AX)
        using communication protocols TTL or RS485.
        
        More precisely, this class can be used to:
            * open/close the communication
            * send (resp. receive) instruction (resp. status) packets
    
        """
    __used_ports = set()
    
    # MARK: - Open/Close and Flush the communication
    
    def __init__(self, port, baudrate=1000000, timeout=0.05):
        """ At instanciation, it opens the serial port and sets the communication parameters.
            
            .. warning:: The port can only be accessed by a single DynamixelIO instance.
                
            :param string port: the serial port to use (e.g. Unix (/dev/tty...), Windows (COM...)).
            :param int baudrate: default for new motors: 57600, for PyPot motors: 1000000
            :param float timeout: read timeout in seconds
            
            :raises: DynamixelError (when port is already used)
            
            """
        if port in self.__used_ports:
            raise DynamixelError('port already used {}'.format(port))
        
        self._serial = serial.Serial(port, baudrate, timeout=timeout)
        self._serial_lock = threading.Lock()
        
        self.__used_ports.add(port)

    def __del__(self):
        self.close()

    def __repr__(self):
        return ('<DXL IO: closed={self.closed}, '
                'port="{self.port}", '
                'baudrate={self.baudrate}, '
                'timeout={self.timeout}>').format(self=self)


    def close(self):
        """ Closes the serial communication if opened. """
        if not self.closed:
            with self._serial_lock:
                self._serial.close()
                self.__used_ports.remove(self.port)

    def _flush(self):
        self._serial.flushInput()
        self._serial.flushOutput()

    def flush(self):
        """ Flushes the serial communication (both input and output).
            
            .. note:: You can use this method after a communication issue, such as a timeout, to refresh the bus.
            
            """
        if self.closed:
            raise DynamixelError('attempt to flush a closed serial communication')
        
        with self._serial_lock:
            self._flush()

    # MARK: Properties of the serial communication

    @property
    def port(self):
        return self._serial.port
            
    @property
    def baudrate(self):
        return self._serial.baudrate
            
    @baudrate.setter
    def baudrate(self, value):
        if self.closed:
            raise DynamixelError('attempt to change baudrate on a closed serial communication')

        with self._serial_lock:
            self._serial.baudrate = value
            
    @property
    def timeout(self):
        return self._serial.timeout
            
    @timeout.setter
    def timeout(self, value):
        if self.closed:
            raise DynamixelError('attempt to change timeout on a closed serial communication')

        with self._serial_lock:
            self._serial.timeout = value
            
    @property
    def closed(self):
        return not (hasattr(self, '_serial') and self._serial.isOpen())


    # MARK: - Send/Receive packet

    def send_packet(self, instruction_packet, wait_for_status_packet=True):
        """ Sends an instruction packet and receives the status packet. """
        if self.closed:
            raise DynamixelError('try to send a packet on a closed serial communication')
    
        with self._serial_lock:
            self._flush()

            data = instruction_packet.to_string()
            nbytes = self._serial.write(data)
            if len(data) != nbytes:
                raise DynamixelCommunicationError('instruction packet not entirely sent',
                                                  instruction_packet)

            if not wait_for_status_packet:
                return

            data = self._serial.read(DynamixelPacketHeader.length)
            if not data:
                raise DynamixelTimeoutError(instruction_packet)
        
            try:
                header = DynamixelPacketHeader.from_string(data)
                data += self._serial.read(header.packet_length)
                status_packet = DynamixelStatusPacket.from_string(data)
                    
            except ValueError:
                raise DynamixelCommunicationError('could not parse received data {}'.format(map(ord, data)),
                                                  instruction_packet)

            return status_packet




DynamixelControl = namedtuple('DynamixelControl', ('name',
                                                   'address', 'length', 'nb_elem',
                                                   'access',
                                                   'models',
                                                   'dxl_to_si', 'si_to_dxl'))

class DynamixelAccess(object):
    readonly, writeonly, readwrite = range(3)



class DynamixelIO(_DynamixelIO):
    """ This class handles the higher-level communication with robotis motors.
        
        More precisely, you can use it to:
            * discover motors (ping, ping_any or scan)
            * access the different control (read, sync read, write and sync write)
        
        This class also transmit the errors (communication, timeout or motor errors)
        to a DynamixelErrorHandler.
        
        """
    __controls = {}

    def __init__(self, port, baudrate=1000000, timeout=0.05, error_handler_cls=BaseErrorHandler):
        _DynamixelIO.__init__(self, port, baudrate, timeout)
        self.error_handler = error_handler_cls()
    
    
    # MARK: - Motor discovery
    
    def ping(self, motor_id):
        """ Pings the motor with the specified id. """
        self._check_motor_id(motor_id)
        
        pp = DynamixelPingPacket(motor_id)
        try:
            _DynamixelIO.send_packet(self, pp)
            return True
        except DynamixelTimeoutError:
            return False

    def ping_any(self):
        """ Ping the broadcast address to find the id of any motor on the bus. """
        pp = DynamixelPingPacket(DynamixelBroadcast)
        try:
            sp = _DynamixelIO.send_packet(self, pp)

            # As all motors on the bus will answer, we force a flush
            # to clean all remaining messages.
            time.sleep(self.timeout)
            self.flush()
            
            if sp:
                return sp.id

        except DynamixelTimeoutError:
            pass

    def scan(self, ids=range(254)):
        """ Pings all motor ids (by default, finds all motors on the bus). """
        return filter(self.ping, ids)
    
    def _lazy_get_model(self, motor_id):
        if not hasattr(self, '_known_models'):
            self._known_models = {}
        
        if not motor_id in self._known_models:
            control = self.__controls['model']
            
            rp = DynamixelReadDataPacket(motor_id, control.address, control.length)
            sp = self.send_packet(rp)
                
            if not sp:
                return
                
            value = dxl_decode(sp.parameters)
            self._known_models[motor_id] = control.dxl_to_si(value, None)

        return self._known_models[motor_id]

    # MARK: Specific controls
    
    def set_id(self, motor_id, new_id):
        """ Changes the id of a motor (each id must be unique on the bus). """
        if self.ping(new_id):
            raise ValueError('id {} is already used.'.format(new_id))

        DynamixelIO._set_id(self, motor_id, new_id)
        
        if motor_id in self._known_models:
            self._known_models[new_id] = self._known_models[motor_id]
            del self._known_models[motor_id]

    def set_sync_id(self, *id_new_id_couples):
        """ Synchronously changes the ids of motors (each id must be unique on the bus). """
        _, new_ids = zip(*id_new_id_couples)

        for new_id in new_ids:
            if self.ping(new_id):
                raise ValueError('id {} is already used.'.format(new_id))
                    
        DynamixelIO._set_sync_id(self, *id_new_id_couples)
            
        for old_id, new_id in id_new_id_couples:
            if old_id in self._known_models:
                self._known_models[new_id] = self._known_models[old_id]
                del self._known_models[old_id]


    # MARK: - Override sending method to handle errors

    def send_packet(self, instruction_packet, wait_for_status_packet=True):
        """ Sends an instruction packet and receives the status packet. 
            
            The possible errors (such as communication or motor errors) are transmitted to the error handler.
            
            .. note:: In case of communication errors for instance, this method will not return anything. So, you should always check if a status packet has been returned.
            
            """
        try:
            sp = _DynamixelIO.send_packet(self, instruction_packet, wait_for_status_packet)
                
            if sp and sp.error:
                errors = decode_error(sp.error)
                for e in errors:
                    handler_name = 'handle_{}'.format(e.lower().replace(' ', '_'))
                    f = operator.methodcaller(handler_name, instruction_packet)
                    f(self.error_handler)
    
            return sp

        except DynamixelTimeoutError as e:
            self.error_handler.handle_timeout(e)

        except DynamixelCommunicationError as e:
            self.error_handler.handle_communication_error(e)


    # MARK: - Accessor Generation

    @classmethod
    def _generate_accessors(cls, control):
        cls.__controls[control.name] = control
        
        if control.access in (DynamixelAccess.readonly, DynamixelAccess.readwrite):
            cls._generate_getter(control)
            cls._generate_sync_getter(control)

        if control.access in (DynamixelAccess.writeonly, DynamixelAccess.readwrite):
            cls._generate_setter(control)
            cls._generate_sync_setter(control)

    @classmethod
    def _generate_getter(cls, control):
        def getter(self, motor_id):
            model = self._lazy_get_model(motor_id)
            if not model:
                return
            self._control_exists_for_model(control, model)
            self._check_motor_id(motor_id)
        
            rp = DynamixelReadDataPacket(motor_id, control.address, control.length * control.nb_elem)
            sp = self.send_packet(rp)
                
            if not sp:
                return

            value = dxl_decode_all(sp.parameters, control.nb_elem)
            return control.dxl_to_si(value, model)

        func_name = 'get_{}'.format(control.name.replace(' ', '_'))
        func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
        getter.func_doc = 'Retrives {} from the motor with the specified id.'.format(control.name)
        getter.func_name = func_name
        setattr(cls, func_name, getter)

    @classmethod
    def _generate_sync_getter(cls, control):
        def sync_getter(self, *ids):
            models = map(self._lazy_get_model, ids)
            if None in models:
                return
            [self._control_exists_for_model(control, model) for model in set(models)]
            [self._check_motor_id(motor_id) for motor_id in ids]

            srp = DynamixelSyncReadPacket(ids, control.address, control.length * control.nb_elem)
            sp = self.send_packet(srp)
    
            if not sp:
                return

            values = list(itertools.izip(*([iter(sp.parameters)] * control.length * control.nb_elem)))
            values = [dxl_decode_all(value, control.nb_elem) for value in values]
            values = [control.dxl_to_si(value, model) for value, model in zip(values, models)]

            return tuple(values)

        func_name = 'get_sync_{}'.format(control.name.replace(' ', '_'))
        func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
        sync_getter.func_doc = 'Synchronously retrives {} from the motors with the specified ids.'.format(control.name)
        sync_getter.func_name = func_name
        setattr(cls, func_name, sync_getter)

    @classmethod
    def _generate_setter(cls, control):
        def setter(self, motor_id, value):
            model = self._lazy_get_model(motor_id)
            if not model:
                return
            self._control_exists_for_model(control, model)
            self._check_motor_id(motor_id)
                  
            value = control.si_to_dxl(value, model)
            value = dxl_code_all(value, control.length, control.nb_elem)
                    
            wp = DynamixelWriteDataPacket(motor_id, control.address, value)
            sp = self.send_packet(wp)
            
        func_name = 'set_{}'.format(control.name.replace(' ', '_'))
        func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
        setter.func_doc = 'Sets {} to the motor with the specified id.'.format(control.name)
        setter.func_name = func_name
        setattr(cls, func_name, setter)

    @classmethod
    def _generate_sync_setter(cls, control):
        def sync_setter(self, *id_value_couples):
            ids, values = zip(*id_value_couples)
            
            models = map(self._lazy_get_model, ids)
            if None in models:
                return
            [self._control_exists_for_model(control, model) for model in set(models)]
            [self._check_motor_id(motor_id) for motor_id in ids]

            values = map(control.si_to_dxl, values, models)
                    
            data = []
            for motor_id, value in zip(ids, values):
                    data.extend(itertools.chain((motor_id, ),
                                                dxl_code_all(value, control.length, control.nb_elem)))
                    
            swp = DynamixelSyncWritePacket(control.address, control.length * control.nb_elem, data)
            self.send_packet(swp, wait_for_status_packet=False)
        
        func_name = 'set_sync_{}'.format(control.name.replace(' ', '_'))
        func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
        sync_setter.func_doc = 'Synchronously sets {} to the motors with the specified ids.'.format(control.name)
        sync_setter.func_name = func_name
        setattr(cls, func_name, sync_setter)

    # MARK: - Various checking
    
    def _control_exists_for_model(self, control, model):
        if model not in control.models:
            raise DynamixelError('try to access {} that does not exist on model {}'.format(control.name, model))
    
    def _check_motor_id(self, motor_id):
        if not (isinstance(motor_id, int) and 0 <= motor_id <= 253):
            raise ValueError('motor id should be in [0, 253]')



# MARK: - Dynamixel Errors

class DynamixelError(Exception):
    pass

class DynamixelCommunicationError(DynamixelError):
    def __init__(self, message, instruction_packet):
        self.message = message
        self.instruction_packet = instruction_packet

    def __str__(self):
        return '{self.message} after sending {self.instruction_packet}'.format(self=self)


class DynamixelTimeoutError(DynamixelCommunicationError):
    def __init__(self, instruction_packet):
        DynamixelCommunicationError.__init__(self, 'timeout occured', instruction_packet)

    def __str__(self):
        return 'after sending {}'.format(self.instruction_packet)


# MARK: - Generate the accessors

def add_register(name,
                 address, length=2, nb_elem=1,
                 access=DynamixelAccess.readwrite,
                 models=set(dynamixelModels.values()),
                 dxl_to_si=lambda val, model: val,
                 si_to_dxl=lambda val, model: val):
    
    control = DynamixelControl(name,
                               address, length, nb_elem,
                               access,
                               models,
                               dxl_to_si, si_to_dxl)
    
    DynamixelIO._generate_accessors(control)

add_register('model',
             address=0x00,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_model)

add_register('firmware',
             address=0x02, length=1,
             access=DynamixelAccess.readonly)

add_register('id',
             address=0x03, length=1)

add_register('baudrate',
             address=0x04, length=1,
             dxl_to_si=dxl_to_baudrate,
             si_to_dxl=baudrate_to_dxl)

add_register('return delay time',
             address=0x05, length=1,
             dxl_to_si=dxl_to_rdt,
             si_to_dxl=rdt_to_dxl)

#add_register('cw angle limit',
#             address=0x06,
#             dxl_to_si=dxl_to_degree,
#             si_to_dxl=degree_to_dxl)

#add_register('ccw angle limit',
#             address=0x08,
#             dxl_to_si=dxl_to_degree,
#             si_to_dxl=degree_to_dxl)

add_register('angle limit',
             address=0x06, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_degree(value[1], model)),
             si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                             degree_to_dxl(value[1], model)))

add_register('highest limit temperature',
             address=0x0B, length=1,
             dxl_to_si=dxl_to_temperature,
             si_to_dxl=temperature_to_dxl)

#add_register('lowest limit voltage',
#             address=0x0C, length=1,
#             dxl_to_si=dxl_to_voltage,
#             si_to_dxl=voltage_to_dxl)

#add_register('highest limit voltage',
#             address=0x0D, length=1,
#             dxl_to_si=dxl_to_voltage,
#             si_to_dxl=voltage_to_dxl)

add_register('limit voltage',
             address=0x0C, length=1, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_voltage(value[0], model),
                                             dxl_to_voltage(value[1], model)),
             si_to_dxl=lambda value, model: (voltage_to_dxl(value[0], model),
                                             voltage_to_dxl(value[1], model)))

add_register('max torque',
             address=0x0E,
             dxl_to_si=dxl_to_torque,
             si_to_dxl=torque_to_dxl)

add_register('status return level',
             address=0x10, length=1,
             dxl_to_si=dxl_to_status,
             si_to_dxl=status_to_dxl)

add_register('alarm LED',
             address=0x11, length=1,
             dxl_to_si=dxl_to_alarm,
             si_to_dxl=alarm_to_dxl)

add_register('alarm shutdown',
             address=0x12, length=1,
             dxl_to_si=dxl_to_alarm,
             si_to_dxl=alarm_to_dxl)

add_register('torque_enable',
             address=0x18, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl)

add_register('LED',
             address=0x19, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl)

#add_register('D gain',
#             address=0x1A, length=1,
#             models=('MX-28',))

#add_register('I gain',
#             address=0x1B, length=1,
#             models=('MX-28', ))

#add_register('P gain',
#             address=0x1C, length=1,
#             models=('MX-28', ))

add_register('pid gain',
             address=0x1A, length=1, nb_elem=3,
             models=('MX-28', ))

add_register('cw compliance margin',
             address=0x1A, length=1,
             models=('AX-12', 'RX-28', 'RX-64'))

add_register('ccw compliance margin',
             address=0x1B, length=1,
             models=('AX-12', 'RX-28', 'RX-64'))

add_register('cw compliance slope',
             address=0x1C, length=1,
             models=('AX-12', 'RX-28', 'RX-64'))

add_register('ccw compliance slope',
             address=0x1D, length=1,
             models=('AX-12', 'RX-28', 'RX-64'))

add_register('goal position',
             address=0x1E,
             dxl_to_si=dxl_to_degree,
             si_to_dxl=degree_to_dxl)

add_register('moving speed',
             address=0x20,
             dxl_to_si=dxl_to_speed,
             si_to_dxl=speed_to_dxl)

add_register('torque limit',
             address=0x22,
             dxl_to_si=dxl_to_torque,
             si_to_dxl=torque_to_dxl)

add_register('goal position speed load',
             address=0x1E, nb_elem=3,
             dxl_to_si=dxl_to_degree_speed_load,
             si_to_dxl=degree_speed_load_to_dxl)

add_register('present position',
             address=0x24,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_degree)

add_register('present speed',
             address=0x26,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_oriented_speed)

add_register('present load',
             address=0x28,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_oriented_load)

add_register('present position speed load',
             address=0x24, nb_elem=3,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_oriented_degree_speed_load)

add_register('present voltage',
             address=0x2A,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_voltage)

add_register('present temperature',
             address=0x2B,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_temperature)

add_register('moving',
             address=0x2E,
             access=DynamixelAccess.readonly,
             dxl_to_si=dxl_to_bool)

add_register('lock',
             address=0x2F,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl)




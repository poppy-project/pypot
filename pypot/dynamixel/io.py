# -*- coding: utf-8 -*-

import time
import array
import serial
import operator
import platform
import itertools
import threading

from collections import namedtuple
from contextlib import contextmanager


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
        self._serial_lock = threading.Lock()
        self.open(port, baudrate, timeout)

    def __del__(self):
        self.close()

    def __repr__(self):
        return ('<DXL IO: closed={self.closed}, '
                'port="{self.port}", '
                'baudrate={self.baudrate}, '
                'timeout={self.timeout}>').format(self=self)


    def open(self, port, baudrate=1000000, timeout=0.05):
        with self._serial_lock:
            self.close(_force_lock=True)

            if port in self.__used_ports:
                raise DynamixelError('port already used {}'.format(port))            
        
            self._serial = serial.Serial(port, baudrate, timeout=timeout)
            self.__used_ports.add(port)

    
    def close(self, _force_lock=False):
        """ Closes the serial communication if opened. """
        if not self.closed:
            with self.__force_lock(_force_lock) or self._serial_lock:
                self._serial.close()
                self.__used_ports.remove(self.port)

    def flush(self, _force_lock=False):
        """ Flushes the serial communication (both input and output).
            
            .. note:: You can use this method after a communication issue, such as a timeout, to refresh the bus.
            
            """
        if self.closed:
            raise DynamixelError('attempt to flush a closed serial communication')
        
        with self.__force_lock(_force_lock) or self._serial_lock:
            self._serial.flushInput()
            self._serial.flushOutput()
                
    def __force_lock(self, condition):
        @contextmanager
        def with_True():
            yield True
                
        return with_True() if condition else False

    # MARK: Properties of the serial communication

    @property
    def port(self):
        return self._serial.port
    
    @port.setter
    def port(self, value):
        self.open(value, self.baudrate, self.timeout)
            
    @property
    def baudrate(self):
        return self._serial.baudrate
            
    @baudrate.setter
    def baudrate(self, value):
        self.open(self.port, value, self.timeout)
            
    @property
    def timeout(self):
        return self._serial.timeout
            
    @timeout.setter
    def timeout(self, value):
        self.open(self.port, self.baudrate, value)
            
    @property
    def closed(self):
        return not (hasattr(self, '_serial') and self._serial.isOpen())


    # MARK: - Send/Receive packet

    def _send_packet(self,
                     instruction_packet, wait_for_status_packet=True,
                     _force_lock=False):
        """ Sends an instruction packet and receives the status packet. """
        if self.closed:
            raise DynamixelError('try to send a packet on a closed serial communication')
    
        with self.__force_lock(_force_lock) or self._serial_lock:
            self.flush(_force_lock=True)

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




_DynamixelControl = namedtuple('DynamixelControl', ('name',
                                                    'address', 'length', 'nb_elem',
                                                    'access',
                                                    'models',
                                                    'dxl_to_si', 'si_to_dxl',
                                                    'getter_name', 'setter_name'))

class _DynamixelAccess(object):
    readonly, writeonly, readwrite = range(3)



class DynamixelIO(_DynamixelIO):
    """ This class handles the higher-level communication with robotis motors.
        
        More precisely, you can use it to:
            * discover motors (ping or scan)
            * access the different control (read, sync read, write and sync write)
        
        This class also transmit the errors (communication, timeout or motor errors)
        to a DynamixelErrorHandler.
        
        """
    __controls = {}

    def __init__(self,
                 port, baudrate=1000000, timeout=0.05,
                 error_handler_cls=BaseErrorHandler,
                 sync_read=True):
        
        _DynamixelIO.__init__(self, port, baudrate, timeout)

        self._known_models = {}
        self._error_handler = error_handler_cls()
        self._sync_read = sync_read
    
    if platform.system() == 'Darwin':
        def open(self, port, baudrate=1000000, timeout=0.05):
            """ Tries to connect to port until it succeeds to ping any motor on the bus.
                
                This is  used to circumvent a bug with the driver for the USB2AX on Mac.
                
                .. warn:: If no motor is connected on the bus, this will run forever!!!
                
                """
            pp = DynamixelPingPacket(DynamixelBroadcast)

            while True:
                _DynamixelIO.open(self, port, baudrate, timeout)
                try:
                    sp = _DynamixelIO._send_packet(self, pp)
                    if sp:
                        break
                except DynamixelTimeoutError:
                    pass
            time.sleep(self.timeout)
            self.flush()

    
    @property
    def port(self):
        return _DynamixelIO.port.fget(self)
    
    @port.setter
    def port(self, value):
        _DynamixelIO.port.fset(self, value)
        self._known_models.clear()    
    
    @property
    def baudrate(self):
        return _DynamixelIO.baudrate.fget(self)
                        
    @baudrate.setter
    def baudrate(self, value):
        _DynamixelIO.baudrate.fset(self, value)
        self._known_models.clear()

    
    # MARK: - Motor discovery
    
    def ping(self, motor_id):
        """ Pings the motor with the specified id. """
        self._check_motor_id(motor_id)
        
        pp = DynamixelPingPacket(motor_id)
        try:
            _DynamixelIO._send_packet(self, pp)
            return True
        except DynamixelTimeoutError:
            return False

    def scan(self, ids=range(254)):
        """ Pings all motor ids (by default it finds all motors on the bus). """
        return filter(self.ping, ids)

    # MARK: Specific controls
            
    def get_model(self, *ids):
        """ Retrieves the model of the specified motors. """
        for motor_id in ids:
            if not motor_id in self._known_models:
                # This allows to circumvent an endless recursion of
                # calls of get_model
                self._known_models[motor_id] = '*'
                self._known_models[motor_id] = self._get_model(motor_id)
        models = tuple(self._known_models[motor_id] for motor_id in ids)
        return models if len(models) > 1 else models[0]
    
    def change_id(self, new_id_for_id):
        """ Changes the id of motors (each id must be unique on the bus). """
        if list(set(new_id_for_id.values())) != new_id_for_id.values():
            raise ValueError('each id must be unique.')

        for new_id in new_id_for_id.itervalues():
            if self.ping(new_id):
                raise ValueError('id {} is already used.'.format(new_id))

        DynamixelIO._change_id(self, new_id_for_id)
        
        for motor_id, new_id in new_id_for_id.iteritems():
            if motor_id in self._known_models:
                self._known_models[new_id] = self._known_models[motor_id]
                del self._known_models[motor_id]

    def change_baudrate(self, baudrate_for_ids):
        """ Changes the baudrate of motors. """
        DynamixelIO._change_baudrate(self, baudrate_for_ids)
        
        for motor_id in baudrate_for_ids.iterkeys():
            if motor_id in self._known_models:
                del self._known_models[motor_id]

    def get_status_return_level(self, *ids):
        """ Retrieves the status level for the motors with the specified ids. """
        # If one motor can not be ping,
        # we send the basic message just to "correctly" receive the timeout.
        if not all(map(self.ping, ids)):
            self._get_status_return_level(*ids)
            return
        
        srl = []
        control = self.__controls['status return level']
        for motor_id in ids:
            try:
                rp = DynamixelReadDataPacket(motor_id, control.address, control.length)
                sp = _DynamixelIO._send_packet(self, rp)
            
                if not sp:
                    return
            
                value = dxl_decode(sp.parameters)
                srl.append(control.dxl_to_si(value, '*'))
            
            except DynamixelTimeoutError:
                srl.append('never')
                    
        return tuple(srl)

    def set_status_return_level(self, srl_for_ids):
        """ Sets status return level for motors with specified ids.
            
            .. warn:: Setting the status return level to "never" will prevent the reception of any message!
            
            """
        # If one motor can not be ping,
        # we send the message just to "correctly" receive the timeout.
        if not all(map(self.ping, srl_for_ids.iterkeys())):
            self._set_status_return_level(srl_for_ids)
            return
        
        control = self.__controls['status return level']

        data = []
        for motor_id, srl in srl_for_ids.iteritems():
            srl = control.si_to_dxl(srl, '*')
            data.extend(itertools.chain((motor_id, ),
                                        dxl_code_all(srl, control.length, control.nb_elem)))

        sp = DynamixelSyncWritePacket(control.address, control.length * control.nb_elem, data)
        self._send_packet(sp, wait_for_status_packet=False)

    def switch_led_on(self, *ids):
        """ Switch on the LED of the motors with the specified ids. """
        DynamixelIO._set_LED(self, dict(itertools.izip(ids, itertools.repeat(True))))
                    
    def switch_led_off(self, *ids):
        """ Switch off the LED of the motors with the specified ids. """
        DynamixelIO._set_LED(self, dict(itertools.izip(ids, itertools.repeat(False))))
                    
    def enable_torque(self, *ids):
        """ Enable torque of the motors with the specified ids. """
        DynamixelIO._set_torque_enable(self, dict(itertools.izip(ids, itertools.repeat(True))))
                    
    def disable_torque(self, *ids):
        """ Disable torque of the motors with the specified ids. """
        DynamixelIO._set_torque_enable(self, dict(itertools.izip(ids, itertools.repeat(False))))
                    
    #    def lock_EEPROM(self, *ids):
    #        """ Lock EEPROM for the motors with the specifeid ids.
    #
    #            .. note:: To unlock the EEPROM again, you need to cycle the power.
    #
    #            """
    #        DynamixelIO._lock_EEPROM(self, dict(itertools.izip(ids, itertools.repeat(True))))

    # MARK: - Override sending method to handle errors

    def _send_packet(self, instruction_packet, wait_for_status_packet=True):
        """ Sends an instruction packet and receives the status packet. 
            
            The possible errors (such as communication or motor errors) are transmitted to the error handler.
            
            .. note:: In case of communication errors for instance, this method will not return anything. So, you should always check if a status packet has been returned.
            
            """
        try:
            sp = _DynamixelIO._send_packet(self, instruction_packet, wait_for_status_packet)
                
            if sp and sp.error:
                errors = decode_error(sp.error)
                for e in errors:
                    handler_name = 'handle_{}'.format(e.lower().replace(' ', '_'))
                    f = operator.methodcaller(handler_name, instruction_packet)
                    f(self._error_handler)
    
            return sp

        except DynamixelTimeoutError as e:
            self._error_handler.handle_timeout(e)

        except DynamixelCommunicationError as e:
            self._error_handler.handle_communication_error(e)


    # MARK: - Accessor Generation

    @classmethod
    def _generate_accessors(cls, control):
        cls.__controls[control.name] = control
        
        if control.access in (_DynamixelAccess.readonly, _DynamixelAccess.readwrite):
            cls._generate_getter(control)

        if control.access in (_DynamixelAccess.writeonly, _DynamixelAccess.readwrite):
            cls._generate_setter(control)


    @classmethod
    def _generate_getter(cls, control):
        def getter(self, *ids):
            models = self.get_model(*ids)
            if not models or (len(models) > 1 and None in models):
                return

            [self._control_exists_for_model(control, model) for model in set(models)]
            [self._check_motor_id(motor_id) for motor_id in ids]
                    
            if self._sync_read and len(ids) > 1:
                rp = DynamixelSyncReadPacket(ids, control.address, control.length * control.nb_elem)
                sp = self._send_packet(rp)
                    
                if not sp:
                    return
                
                values = sp.parameters
        
            else:
                values = []
                for motor_id in ids:
                    rp = DynamixelReadDataPacket(motor_id, control.address, control.length * control.nb_elem)
                    sp = self._send_packet(rp)
                
                    if not sp:
                        return

                    values.extend(sp.parameters)
    
            values = list(itertools.izip(*([iter(values)] * control.length * control.nb_elem)))
            values = [dxl_decode_all(value, control.nb_elem) for value in values]
            values = [control.dxl_to_si(value, model) for value, model in zip(values, models)]
                
            return tuple(values) if len(values) > 1 else values[0]

        func_name = control.getter_name if control.getter_name else 'get_{}'.format(control.name.replace(' ', '_'))
        func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
        getter.func_doc = 'Retrives {} from the motor with the specified id.'.format(control.name)
        getter.func_name = func_name
        setattr(cls, func_name, getter)


    @classmethod
    def _generate_setter(cls, control):
        def setter(self, value_for_id):
            ids, values = zip(*value_for_id.items())
            
            models = self.get_model(*ids)
            if not models or (len(models) > 1 and None in models):
                return
            [self._control_exists_for_model(control, model) for model in set(models)]
            [self._check_motor_id(motor_id) for motor_id in ids]

            values = map(control.si_to_dxl, values, models)
            data = []
            for motor_id, value in zip(ids, values):
                data.extend(itertools.chain((motor_id, ),
                                            dxl_code_all(value, control.length, control.nb_elem)))

            wp = DynamixelSyncWritePacket(control.address, control.length * control.nb_elem, data)
            sp = self._send_packet(wp, wait_for_status_packet=False)
            
        func_name = control.setter_name if control.setter_name else 'set_{}'.format(control.name.replace(' ', '_'))
        func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
        setter.func_doc = 'Sets {} to the motors with the specified id.'.format(control.name)
        setter.func_name = func_name
        setattr(cls, func_name, setter)
            
            
    # MARK: - Various checking
    
    def _control_exists_for_model(self, control, model):
        if model not in control.models and model != '*':
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
                 access=_DynamixelAccess.readwrite,
                 models=set(dynamixelModels.values()),
                 dxl_to_si=lambda val, model: val,
                 si_to_dxl=lambda val, model: val,
                 getter_name=None,
                 setter_name=None):
    
    control = _DynamixelControl(name,
                               address, length, nb_elem,
                               access,
                               models,
                               dxl_to_si, si_to_dxl,
                               getter_name, setter_name)
    
    DynamixelIO._generate_accessors(control)

add_register('model',
             address=0x00,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_model)

add_register('firmware',
             address=0x02, length=1,
             access=_DynamixelAccess.readonly)

add_register('id',
             address=0x03, length=1,
             access=_DynamixelAccess.writeonly,
             setter_name='change_id')

add_register('baudrate',
             address=0x04, length=1,
             access=_DynamixelAccess.writeonly,
             setter_name='change_baudrate',
             si_to_dxl=baudrate_to_dxl)

add_register('return delay time',
             address=0x05, length=1,
             dxl_to_si=dxl_to_rdt,
             si_to_dxl=rdt_to_dxl)

add_register('angle limit',
             address=0x06, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_degree(value[1], model)),
             si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                             degree_to_dxl(value[1], model)))

add_register('highest temperature limit',
             address=0x0B, length=1,
             dxl_to_si=dxl_to_temperature,
             si_to_dxl=temperature_to_dxl)

add_register('voltage limit',
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
             si_to_dxl=bool_to_dxl,
             getter_name='is_torque_enabled',
             setter_name='_set_torque_enable')

add_register('LED',
             address=0x19, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl,
             setter_name='_set_LED',
             getter_name='is_led_on')

add_register('pid gain',
             address=0x1A, length=1, nb_elem=3,
             models=('MX-28', ))

add_register('compliance margin',
             address=0x1A, length=1, nb_elem=2,
             models=('AX-12', 'RX-28', 'RX-64'))

add_register('compliance slope',
             address=0x1C, length=1, nb_elem=2,
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
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_degree)

add_register('present speed',
             address=0x26,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_oriented_speed)

add_register('present load',
             address=0x28,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_oriented_load)

add_register('present position speed load',
             address=0x24, nb_elem=3,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_oriented_degree_speed_load)

add_register('present voltage',
             address=0x2A, length=1,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_voltage)

add_register('present temperature',
             address=0x2B, length=1,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_temperature)

add_register('moving',
             address=0x2E, length=1,
             access=_DynamixelAccess.readonly,
             dxl_to_si=dxl_to_bool,
             getter_name='is_moving')

#add_register('lock',
#             address=0x2F,
#             dxl_to_si=dxl_to_bool,
#             si_to_dxl=bool_to_dxl,
#             getter_name='is_EEPROM_locked',
#             setter_name='lock_EEPROM')

# -*- coding: utf-8 -*-

import serial
import operator
import itertools
import threading

from collections import namedtuple
from contextlib import contextmanager


from pypot.dynamixel.conversion import *
from pypot.dynamixel.packet import *



_DynamixelControl = namedtuple('_DynamixelControl', ('name',
                                                     'address', 'length', 'nb_elem',
                                                     'access',
                                                     'models',
                                                     'dxl_to_si', 'si_to_dxl',
                                                     'getter_name', 'setter_name'))

class _DynamixelAccess(object):
    readonly, writeonly, readwrite = range(3)



class DynamixelIO(object):
    """ This class handles the low-level communication with robotis motors.
        
        Using a USB communication device such as USB2DYNAMIXEL or USB2AX,
        you can open serial communication with robotis motors (MX, RX, AX)
        using communication protocols TTL or RS485.
        
        More precisely, this class can be used to:
            * open/close the communication
            * discover motors (ping or scan)
            * access the different control (read and write)
        
        .. note:: This class can be used as a context manager (e.g. with DynamixelIO(...) as dxl_io:)
    
        """
    __used_ports = set()
    
    # MARK: - Open, Close and Flush the communication
    
    def __init__(self,
                 port, baudrate=1000000, timeout=0.05,
                 use_sync_read=True,
                 error_handler=None,
                 convert=True):
        """ At instanciation, it opens the serial port and sets the communication parameters.
            
            .. warning:: The port can only be accessed by a single DynamixelIO instance.
                
            :param string port: the serial port to use (e.g. Unix (/dev/tty...), Windows (COM...)).
            :param int baudrate: default for new motors: 57600, for PyPot motors: 1000000
            :param float timeout: read timeout in seconds
            :param bool use_sync_read: whether or not to use the SYNC_READ instruction
            :param DynamixelErrorHandler error_handler: set a handler that will receive the different errors
            :param bool convert: whether or not convert values to si
                        
            """
        self._known_models = {}
        self._known_mode = {}

        self._sync_read = use_sync_read
        self._error_handler = error_handler
        self._convert = convert

        self._serial_lock = threading.Lock()
        self.open(port, baudrate, timeout)
    
    def __enter__(self):
        return self

    def __del__(self):
        self.close()
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return ('<DXL IO: closed={self.closed}, '
                'port="{self.port}", '
                'baudrate={self.baudrate}, '
                'timeout={self.timeout}>').format(self=self)
    
    def open(self, port, baudrate=1000000, timeout=0.05):
        """ Opens a new serial communication (closes the previous communication if needed).
            
            .. note:: Only a single communication can be opened to a port (raises DynamixelError if the port is already used).
            """
        self._known_models.clear()
        self._known_mode.clear()

        with self._serial_lock:
            self.close(_force_lock=True)

            if port in self.__used_ports:
                raise DynamixelError('port already used {}'.format(port))            
        
            self._serial = serial.Serial(port, baudrate, timeout=timeout)
            self.__used_ports.add(port)

        # Tries to connect to port until it succeeds to ping any motor on the bus.
        # This is  used to circumvent a bug with the driver for the USB2AX on Mac.
        # Warning: If no motor is connected on the bus, this will run forever!!!
        import platform
        if platform.system() == 'Darwin':
            import time
            
            if not self.ping(DynamixelBroadcast):
                self.close()
                self.open(port, baudrate, timeout)
            else:
                time.sleep(self.timeout)
                self.flush()
    
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

    # MARK: - Motor discovery
    
    def ping(self, id):
        """ Pings the motor with the specified id. """
        pp = DynamixelPingPacket(id)
        try:
            self._send_packet(pp, error_handler=None)
            return True
        except DynamixelTimeoutError:
            return False

    def scan(self, ids=range(254)):
        """ Pings all ids, by default it finds all the motors connected to the bus. """
        return filter(self.ping, ids)
    
    # MARK: - Specific Getter / Setter
    
    def get_model(self, *ids):
        """ Retrieves the model of the specified motors. """
        to_get_ids = filter(lambda id: id not in self._known_models, ids)
        
        models = map(dxl_to_model, self._get_model(*to_get_ids, convert=False))
        self._known_models.update(zip(to_get_ids, models))
        
        return tuple(self._known_models[id] for id in ids)

    def change_id(self, new_id_for_id):
        """ Changes the id of the specified motors (each id must be unique on the bus). """
        if len(set(new_id_for_id.values())) < len(new_id_for_id):
            raise ValueError('each id must be unique.')
        
        for new_id in new_id_for_id.itervalues():
            if self.ping(new_id):
                raise ValueError('id {} is already used.'.format(new_id))
        
        self._change_id(new_id_for_id)
        
        for motor_id, new_id in new_id_for_id.iteritems():
            if motor_id in self._known_models:
                self._known_models[new_id] = self._known_models[motor_id]
                del self._known_models[motor_id]
            if motor_id in self._known_mode:
                self._known_mode[new_id] = self._known_mode[motor_id]
                del self._known_mode[motor_id]

    def change_baudrate(self, baudrate_for_ids):
        """ Changes the baudrate of the specified motors. """
        self._change_baudrate(baudrate_for_ids)

        for motor_id in baudrate_for_ids.iterkeys():
            if motor_id in self._known_models:
                del self._known_models[motor_id]
            if motor_id in self._known_mode:
                del self._known_mode[motor_id]

    def get_status_return_level(self, *ids, **kwargs):
        """ Retrieves the status level for the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        srl = []
        for id in ids:
            try:
                srl.extend(self._get_status_return_level(id, error_handler=None, convert=convert))
            except DynamixelTimeoutError as e:
                if self.ping(id):
                    srl.append('never' if convert else 0)
                else:
                    if self._error_handler:
                        self._error_handler.handle_timeout(e)
                        return ()
                    else:
                        raise e

        return tuple(srl)
    
    def set_status_return_level(self, srl_for_id, **kwargs):
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        if convert:
            srl_for_id = dict(zip(srl_for_id.keys(),
                                  map(lambda s: ('never', 'read', 'always').index(s), srl_for_id.values())))
        self._set_status_return_level(srl_for_id, convert=False)
    
    def get_mode(self, *ids):
        """ Retrieves the mode ('joint' or 'wheel') of the specified motors. """
        to_get_ids = filter(lambda id: id not in self._known_mode, ids)
        limits = self.get_angle_limit(*to_get_ids, convert=False)
        modes = ('wheel' if limit == (0, 0) else 'joint' for limit in limits)
        
        self._known_mode.update(zip(to_get_ids, modes))
            
        return tuple(self._known_mode[id] for id in ids)
            
    def set_wheel_mode(self, *ids):
        """ Sets the specified motors to wheel mode. """
        self._set_mode(dict(itertools.izip(ids, itertools.repeat('wheel'))))
            
    def set_joint_mode(self, *ids):
        """ Sets the specified motors to joint mode. """
        self._set_mode(dict(itertools.izip(ids, itertools.repeat('joint'))))

    def _set_mode(self, mode_for_id):
        models = map(lambda m: 'MX' if m.startswith('MX') else '*',
                     self.get_model(*mode_for_id.keys()))
        pos_max = map(lambda m: position_range[m][0], models)
        limits = ((0, 0) if mode == 'wheel' else (0, pos_max[i] - 1)
                  for i, mode in enumerate(mode_for_id.itervalues()))

        self._set_angle_limit(dict(zip(mode_for_id.keys(), limits)), convert=False)
        self._known_mode.update(mode_for_id.items())

    def set_angle_limit(self, limit_for_id, **kwargs):
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert

        if 'wheel' in self.get_mode(*limit_for_id.keys()):
            raise ValueError('can not change the angle limit of a motor in wheel mode')
        
        if (0, 0) in limit_for_id.values():
            raise ValueError('can not set limit to (0, 0)')
        
        self._set_angle_limit(limit_for_id, convert=convert)

    def switch_led_on(self, *ids):
        """ Switch on the LED of the motors with the specified ids. """
        self._set_LED(dict(itertools.izip(ids, itertools.repeat(True))))
            
    def switch_led_off(self, *ids):
        """ Switch off the LED of the motors with the specified ids. """
        self._set_LED(dict(itertools.izip(ids, itertools.repeat(False))))
            
    def enable_torque(self, *ids):
        """ Enable torque of the motors with the specified ids. """
        self._set_torque_enable(dict(itertools.izip(ids, itertools.repeat(True))))
            
    def disable_torque(self, *ids):
        """ Disable torque of the motors with the specified ids. """
        self._set_torque_enable(dict(itertools.izip(ids, itertools.repeat(False))))
            

    # MARK: - Generic Getter / Setter

    @classmethod
    def _generate_accessors(cls, control):        
        if control.access in (_DynamixelAccess.readonly, _DynamixelAccess.readwrite):
            def my_getter(self, *ids, **kwargs):                    
                return self._get_control_value(control, *ids, **kwargs)
            
            func_name = control.getter_name if control.getter_name else 'get_{}'.format(control.name.replace(' ', '_'))
            func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
            my_getter.func_doc = 'Retrives {} from the specified motors.'.format(control.name)
            my_getter.func_name = func_name
            setattr(cls, func_name, my_getter)

        if control.access in (_DynamixelAccess.writeonly, _DynamixelAccess.readwrite):
            def my_setter(self, value_for_id, **kwargs):
                self._set_control_value(control, value_for_id, **kwargs)

            func_name = control.setter_name if control.setter_name else 'set_{}'.format(control.name.replace(' ', '_'))
            func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
            my_setter.func_doc = 'Sets {} to the specified motors.'.format(control.name)
            my_setter.func_name = func_name
            setattr(cls, func_name, my_setter)
                    
    def _get_control_value(self, control, *ids, **kwargs):
        error_handler = kwargs['error_handler'] if ('error_handler' in kwargs) else self._error_handler
        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert

        if self._sync_read and len(ids) > 1:
            rp = DynamixelSyncReadPacket(ids, control.address, control.length * control.nb_elem)
            sp = self._send_packet(rp, error_handler=error_handler)
            
            if not sp:
                return ()
            
            values = sp.parameters
        
        else:
            values = []
            for motor_id in ids:
                rp = DynamixelReadDataPacket(motor_id, control.address, control.length * control.nb_elem)
                sp = self._send_packet(rp, error_handler=error_handler)
                
                if not sp:
                    return ()
                
                values.extend(sp.parameters)

        values = list(itertools.izip(*([iter(values)] * control.length * control.nb_elem)))
        values = [dxl_decode_all(value, control.nb_elem) for value in values]

        # when using SYNC_READ instead of getting a timeout
        # a non existing motor will "return" the maximum value
        if self._sync_read:
            max_val = 2 ** (8 * control.length) - 1
            if max_val in (itertools.chain(*values) if control.nb_elem > 1 else values):
                e = DynamixelTimeoutError(rp)
                if self._error_handler:
                    self._error_handler.handle_timeout(e)
                else:
                    raise e
    
        if convert:
            models = self.get_model(*ids)
            if not models:
                return ()

            values = map(control.dxl_to_si, values, models)
    
        return tuple(values)

    def _set_control_value(self, control, value_for_id, **kwargs):
        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert

        if convert:
            models = self.get_model(*value_for_id.keys())
            if not models:
                return
                
            value_for_id = dict(zip(value_for_id.keys(),
                                    map(control.si_to_dxl, value_for_id.values(), models)))
    
        data = []
        for motor_id, value in value_for_id.iteritems():
            data.extend(itertools.chain((motor_id, ),
                                        dxl_code_all(value, control.length, control.nb_elem)))
    
        wp = DynamixelSyncWritePacket(control.address, control.length * control.nb_elem, data)
        sp = self._send_packet(wp, wait_for_status_packet=False)


    # MARK: - Send/Receive packet

    def __real_send(self, instruction_packet, wait_for_status_packet, _force_lock):
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


    def _send_packet(self,
                    instruction_packet, wait_for_status_packet=True,
                    error_handler=None,
                    _force_lock=False):
        if not error_handler:
            return self.__real_send(instruction_packet, wait_for_status_packet, _force_lock)
        
        try:
            sp = self.__real_send(instruction_packet, wait_for_status_packet, _force_lock)
                
            if sp and sp.error:
                errors = decode_error(sp.error)
                for e in errors:
                    handler_name = 'handle_{}'.format(e.lower().replace(' ', '_'))
                    f = operator.methodcaller(handler_name, instruction_packet)
                    f(error_handler)
                    
                return sp
                
        except DynamixelTimeoutError as e:
            error_handler.handle_timeout(e)
                
        except DynamixelCommunicationError as e:
            error_handler.handle_communication_error(e)




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

def add_control(name,
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


add_control('model',
            address=0x00,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_model)

add_control('firmware',
            address=0x02, length=1,
            access=_DynamixelAccess.readonly)

add_control('id',
            address=0x03, length=1,
            access=_DynamixelAccess.writeonly,
            setter_name='change_id')

add_control('baudrate',
            address=0x04, length=1,
            access=_DynamixelAccess.writeonly,
            setter_name='change_baudrate',
            si_to_dxl=baudrate_to_dxl)

add_control('return delay time',
            address=0x05, length=1,
            dxl_to_si=dxl_to_rdt,
            si_to_dxl=rdt_to_dxl)

add_control('angle limit',
            address=0x06, nb_elem=2,
            dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                            dxl_to_degree(value[1], model)),
            si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                            degree_to_dxl(value[1], model)))

add_control('highest temperature limit',
            address=0x0B, length=1,
            dxl_to_si=dxl_to_temperature,
            si_to_dxl=temperature_to_dxl)

add_control('voltage limit',
            address=0x0C, length=1, nb_elem=2,
            dxl_to_si=lambda value, model: (dxl_to_voltage(value[0], model),
                                            dxl_to_voltage(value[1], model)),
            si_to_dxl=lambda value, model: (voltage_to_dxl(value[0], model),
                                            voltage_to_dxl(value[1], model)))

add_control('max torque',
            address=0x0E,
            dxl_to_si=dxl_to_torque,
            si_to_dxl=torque_to_dxl)

add_control('status return level',
            address=0x10, length=1,
            dxl_to_si=dxl_to_status,
            si_to_dxl=status_to_dxl)

add_control('alarm LED',
            address=0x11, length=1,
            dxl_to_si=dxl_to_alarm,
            si_to_dxl=alarm_to_dxl)

add_control('alarm shutdown',
            address=0x12, length=1,
            dxl_to_si=dxl_to_alarm,
            si_to_dxl=alarm_to_dxl)

add_control('torque_enable',
            address=0x18, length=1,
            dxl_to_si=dxl_to_bool,
            si_to_dxl=bool_to_dxl,
            getter_name='is_torque_enabled',
            setter_name='_set_torque_enable')

add_control('LED',
            address=0x19, length=1,
            dxl_to_si=dxl_to_bool,
            si_to_dxl=bool_to_dxl,
            setter_name='_set_LED',
            getter_name='is_led_on')

add_control('pid gain',
            address=0x1A, length=1, nb_elem=3,
            models=('MX-28', ))

add_control('compliance margin',
            address=0x1A, length=1, nb_elem=2,
            models=('AX-12', 'RX-28', 'RX-64'))

add_control('compliance slope',
            address=0x1C, length=1, nb_elem=2,
            models=('AX-12', 'RX-28', 'RX-64'))

add_control('goal position',
            address=0x1E,
            dxl_to_si=dxl_to_degree,
            si_to_dxl=degree_to_dxl)

add_control('moving speed',
            address=0x20,
            dxl_to_si=dxl_to_speed,
            si_to_dxl=speed_to_dxl)

add_control('torque limit',
            address=0x22,
            dxl_to_si=dxl_to_torque,
            si_to_dxl=torque_to_dxl)

add_control('goal position speed load',
            address=0x1E, nb_elem=3,
            dxl_to_si=dxl_to_degree_speed_load,
            si_to_dxl=degree_speed_load_to_dxl)

add_control('present position',
            address=0x24,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_degree)

add_control('present speed',
            address=0x26,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_oriented_speed)

add_control('present load',
            address=0x28,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_oriented_load)

add_control('present position speed load',
            address=0x24, nb_elem=3,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_oriented_degree_speed_load)

add_control('present voltage',
            address=0x2A, length=1,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_voltage)

add_control('present temperature',
            address=0x2B, length=1,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_temperature)

add_control('moving',
            address=0x2E, length=1,
            access=_DynamixelAccess.readonly,
            dxl_to_si=dxl_to_bool,
            getter_name='is_moving')

#add_control('lock',
#            address=0x2F,
#            dxl_to_si=dxl_to_bool,
#            si_to_dxl=bool_to_dxl,
#            getter_name='is_EEPROM_locked',
#            setter_name='lock_EEPROM')

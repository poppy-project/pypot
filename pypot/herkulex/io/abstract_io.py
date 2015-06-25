# -*- coding: utf-8 -*-

import serial
import logging
import operator
import itertools
import threading
import time

from ..protocol import *

from collections import namedtuple, OrderedDict
from contextlib import contextmanager

from pypot.robot.io import AbstractIO
from ..conversion import *


logger = logging.getLogger(__name__)
# With this logger you should always provide as extra:
# - the port
# - the baudrate
# - the timeout


_HkxControl = namedtuple('_HkxControl', ('name', 'eeprom_ram',
                                         'address', 'length', 'nb_elem',
                                         'access',
                                         'models',
                                         'hkx_to_si', 'si_to_hkx',
                                         'getter_name', 'setter_name'))


class _HkxAccess(object):
    readonly, writeonly, readwrite = range(3)


class AbstractHkxIO(AbstractIO):
    """ Low-level class to handle the serial communication with the dongbu robot motors. """

    __used_ports = set()
    __controls = []
    _protocol = None

    # MARK: - Open, Close and Flush the communication

    def __init__(self,
                 port, baudrate=115200, timeout=0.05,
                 use_sync_read=False,
                 error_handler_cls=None,
                 convert=True):
        """ At instanciation, it opens the serial port and sets the communication parameters.

            :param string port: the serial port to use (e.g. Unix (/dev/tty...), Windows (COM...)).
            :param int baudrate: default 666666 (vs 115200 factory settings) 
            :param float timeout: read timeout in seconds
            :param bool use_sync_read: whether or not to use the SYNC_READ instruction
            :param error_handler: set a handler that will receive the different errors
            :type error_handler: :py:class:`~pypot.herkulex.error.HkxErrorHandler`
            :param bool convert: whether or not convert values to units expressed in the standard system

            :raises: :py:exc:`~pypot.herkulex.io.HkxError` if the port is already used.

            """
        self._known_models = {}
        self._known_mode = {}

        self._sync_read = use_sync_read
        self._error_handler = error_handler_cls() if error_handler_cls else None
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
        return ('<HKX IO: closed={self.closed}, '
                'port="{self.port}", '
                'baudrate={self.baudrate}, '
                'timeout={self.timeout}>').format(self=self)

    def open(self, port, baudrate=115200, timeout=0.05):
        """ Opens a new serial communication (closes the previous communication if needed).

            :raises: :py:exc:`~pypot.herkulex.io.HkxError` if the port is already used.

            """
        self._open(port, baudrate, timeout)
        logger.info("Opening port '%s'", self.port,
                    extra={'port': port,
                           'baudrate': baudrate,
                           'timeout': timeout})

    def _open(self, port, baudrate, timeout, max_recursion=500):
        # Tries to connect to port until it succeeds to ping any motor on the bus
        # Warning: If no motor is connected on the bus, this will run forever!!!
        import platform
        # import time
        import pypot.utils.pypot_time as time
        #TODO: check on Linux and Darwin platforms
        for i in range(max_recursion):
            self._known_models.clear()
            self._known_mode.clear()

            with self._serial_lock:
                self.close(_force_lock=True)

                if port in self.__used_ports:
                    raise HkxError('port already used {}'.format(port))

                self._serial = serial.Serial(port, baudrate, timeout=timeout)
                self.__used_ports.add(port)

            break
        else:
            raise HkxError('could not connect to the port {}'.format(self.port))

    def close(self, _force_lock=False):
        """ Closes the serial communication if opened. """
        if not self.closed:
            with self.__force_lock(_force_lock) or self._serial_lock:
                self._serial.close()
                self.__used_ports.remove(self.port)

            logger.info("Closing port '%s'", self.port,
                        extra={'port': self.port,
                               'baudrate': self.baudrate,
                               'timeout': self.timeout})

    def flush(self, _force_lock=False):
        """ Flushes the serial communication (both input and output). """
        if self.closed:
            raise HkxError('attempt to flush a closed serial communication')

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
        """ Port used by the :class:`~pypot.herkulex.io.HkxIO`. If set, will re-open a new connection. """
        return self._serial.port

    @port.setter
    def port(self, value):
        self.open(value, self.baudrate, self.timeout)

    @property
    def baudrate(self):
        """ Baudrate used by the :class:`~pypot.herkulex.io.HkxIO`. If set, will re-open a new connection. """
        return self._serial.baudrate

    @baudrate.setter
    def baudrate(self, value):
        self.open(self.port, value, self.timeout)

    @property
    def timeout(self):
        """ Timeout used by the :class:`~pypot.herkulex.io.HkxIO`. If set, will re-open a new connection. """
        return self._serial.timeout

    @timeout.setter
    def timeout(self, value):
        self.open(self.port, self.baudrate, value)

    @property
    def closed(self):
        """ Checks if the connection is closed. """
        return not (hasattr(self, '_serial') and self._serial.isOpen())

    # MARK: - Motor discovery

    def ping(self, id):
        """ Pings the motor with the specified id.

            .. note:: The motor id should always be included in [0, 253]. 254 is used for broadcast.

            """
        pp = HkxPingPacket(id)

        try:
            self._send_packet(pp, error_handler=None)
            return True
        except HkxTimeoutError:
            return False


    def scan(self, ids=xrange(254)):
        """ Pings all ids within the specified list, by default it finds all the motors connected to the bus. """
        return [id for id in ids if self.ping(id)]
        
    # MARK: - Specific Getter / Setter

    def get_model(self, ids):
        """ Gets the model for the specified motors. """
        to_get_ids = [i for i in ids if i not in self._known_models]
        models = [hkx_to_model(m) for m in self._get_model(to_get_ids, convert=False)]
        self._known_models.update(zip(to_get_ids, models))
        return tuple(self._known_models[id] for id in ids)

    def change_id(self, new_id_for_id, EEPROM_too = False):
        """ Changes the id of the specified motors (each id must be unique on the bus). """
        if len(set(new_id_for_id.values())) < len(new_id_for_id):
            raise ValueError('each id must be unique.')

        for new_id in new_id_for_id.itervalues():
            if self.ping(new_id):
                raise ValueError('id {} is already used.'.format(new_id))

        if EEPROM_too : 
            self.change_id_EEPROM(new_id_for_id)
            
        self._change_id(new_id_for_id)

        for motor_id, new_id in new_id_for_id.iteritems():
            if motor_id in self._known_models:
                self._known_models[new_id] = self._known_models[motor_id]
                del self._known_models[motor_id]
            if motor_id in self._known_mode:
                self._known_mode[new_id] = self._known_mode[motor_id]
                del self._known_mode[motor_id]
    #TODO: test this function
    def change_baudrate(self, baudrate_for_ids):
        """ Changes the baudrate of the specified motors. """
        self._change_baudrate(baudrate_for_ids)

        for motor_id in baudrate_for_ids:
            if motor_id in self._known_models:
                del self._known_models[motor_id]
            if motor_id in self._known_mode:
                del self._known_mode[motor_id]
    #TODO: test this function
    def get_status_return_level(self, ids, **kwargs):
        """ Gets the status level for the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        srl = []
        for id in ids:
            try:
                srl.extend(self._get_status_return_level((id, ),
                           error_handler=None, convert=convert))
            except HkxTimeoutError as e:
                if self.ping(id):
                    srl.append('never' if convert else 0)
                else:
                    if self._error_handler:
                        self._error_handler.handle_timeout(e)
                        return ()
                    else:
                        raise e

        return tuple(srl)
    #TODO: test this function
    def set_status_return_level(self, srl_for_id, **kwargs):
        """ Sets status return level to the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        if convert:
            srl_for_id = dict(zip(srl_for_id.keys(),
                              [('never', 'read', 'always').index(s) for s in srl_for_id.values()]))
        self._set_status_return_level(srl_for_id, convert=False)

    def switch_led_on(self, ids, color = 'white'):
        """ Switches on the LED of the motors with the specified ids. """
        self.set_LED(dict(zip(ids, itertools.repeat(color))))

    def switch_led_off(self, ids):
        """ Switches off the LED of the motors with the specified ids. """
        self.set_LED(dict(zip(ids, itertools.repeat('off'))))

    def enable_torque(self, ids):
        """ Enables torque of the motors with the specified ids. """
        self.set_torque_enabled(dict(zip(ids, itertools.repeat(True))))

    def disable_torque(self, ids):
        """ Disables torque of the motors with the specified ids. """
        self.set_torque_enabled(dict(zip(ids, itertools.repeat(False))))

    #TODO: add PID gain functions?

    # MARK: - Generic Getter / Setter
    #TODO: create a get_control_table function?

    @classmethod
    def _generate_accessors(cls, control):
        cls.__controls.append(control)

        if control.access in (_HkxAccess.readonly, _HkxAccess.readwrite):
            def my_getter(self, ids, **kwargs):
                return self._get_control_value(control, ids, **kwargs)

            func_name = control.getter_name if control.getter_name else 'get_{}'.format(control.name.replace(' ', '_'))
            func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
            my_getter.__doc__ = 'Gets {} from the specified motors.'.format(control.name)
            my_getter.__name__ = func_name
            setattr(cls, func_name, my_getter)

        if control.access in (_HkxAccess.writeonly, _HkxAccess.readwrite):
            def my_setter(self, value_for_id, **kwargs):
                self._set_control_value(control, value_for_id, **kwargs)

            func_name = control.setter_name if control.setter_name else 'set_{}'.format(control.name.replace(' ', '_'))
            func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
            my_setter.__doc__ = 'Sets {} to the specified motors.'.format(control.name)
            my_setter.__name__ = func_name
            setattr(cls, func_name, my_setter)

    def _get_control_value(self, control, ids, **kwargs):
        if not ids:
            return ()
        error_handler = kwargs['error_handler'] if ('error_handler' in kwargs) else self._error_handler
        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert

        values = []
        for motor_id in ids:
            rp = HkxReadDataPacket(motor_id, control.eeprom_ram, control.address, control.length * control.nb_elem)
            sp = self._send_packet(rp, error_handler=error_handler)

            if not sp:
                return ()
            values.extend(sp.parameters)


        values = list(itertools.izip(*([iter(values)] * control.length * control.nb_elem)))
        values = [hkx_decode_all(value, control.nb_elem) for value in values]

        if not values:
            return ()

        if convert:
            models = self.get_model(ids)
            if not models:
                return ()
            values = [control.hkx_to_si(v, m) for v, m in zip(values, models)]

        return tuple(values)

    def _set_control_value(self, control, value_for_id, **kwargs):
        if not value_for_id:
            return

        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert

        if convert:
            models = self.get_model(value_for_id.keys())
            if not models:
                return

            value_for_id = dict(zip(value_for_id.keys(),
                                    map(control.si_to_hkx, value_for_id.values(), models)))

        for motor_id, value in value_for_id.iteritems():
            dat=hkx_code_all(value, control.length, control.nb_elem)
            wp = HkxWriteDataPacket(motor_id, control.eeprom_ram, control.address, control.length, control.nb_elem, dat)
            self._send_packet(wp, wait_for_status_packet=False)
            
            
    def joint_jog(self, goal_position_time_for_id, **kwargs):
        if not goal_position_time_for_id:
            return

        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert
        set_control_mode_only = kwargs['set_control_mode_only'] if ('set_control_mode_only' in kwargs) else False

        if convert:
            models = self.get_model(goal_position_time_for_id.keys())
            if not models:
                return
                
        t=0
        for id, goal_position_time_led in iter(goal_position_time_for_id.items()):
            pos = goal_position_time_led[0]
            tm = goal_position_time_led[1]
            ld=None
            if len(goal_position_time_led) > 2:
                ld = goal_position_time_led[2]
            
            if convert :
                md = models[t]
                pos = degree_to_hkx(pos, md)
                tm = time_to_hkx(tm, md)
                ld = LED_to_hkx(ld, md)
            
            ld = (ld << 2) #shift bits and set to wheel
            pos_msb = int(pos) >> 8
            pos_lsb = int(pos) & 0xff

            data = (pos_lsb, pos_msb, (set_control_mode_only | ld), id, tm)
            wp = HkxJogPacket(id,HkxInstruction.I_JOG, data)
            self._send_packet(wp, wait_for_status_packet=False)
            t=t+1

    def wheel_jog(self, goal_speed_led_for_id, **kwargs):
        if not goal_speed_led_for_id:
            return

        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert

        if convert:
            models = self.get_model(goal_speed_led_for_id.keys())
            if not models:
                return
                
        t=0
        for id, itm in iter(goal_speed_led_for_id.items()):
            speed = itm[0]
            ld = None
            if len(itm) > 1:
                ld = itm[1]
            
            if convert :
                md = models[t]
                speed = speed_to_hkx(speed, md)
                ld = LED_to_hkx(ld, md)

            ld = (ld << 2) | 0x02 #shift bits and set to wheel
   
            if(speed>0):
                goalspeed_msb = (int(speed)& 0xFF00) >> 8
                goalspeed_lsb = int(speed) & 0xff
            elif(speed<0):
                goalspeed_msb = 64+(255- ((int(speed)& 0xFF00) >> 8))
                goalspeed_lsb = (abs(speed) & 0xff)
            else:
                goalspeed_msb = 0x00
                goalspeed_lsb = 0x00
                ld=ld | 0x01
                
            data = (goalspeed_lsb, goalspeed_msb, ld, id, 0)
            wp = HkxJogPacket(id,HkxInstruction.I_JOG, data)
            self._send_packet(wp, wait_for_status_packet=False)
            t=t+1


    # MARK: - Send/Receive packet
    def __real_send(self, instruction_packet, wait_for_status_packet, _force_lock):
        if self.closed:
            raise HkxError('try to send a packet on a closed serial communication')

        logger.debug('Sending %s', instruction_packet,
                     extra={'port': self.port,
                            'baudrate': self.baudrate,
                            'timeout': self.timeout})

        with self.__force_lock(_force_lock) or self._serial_lock:
            self.flush(_force_lock=True)
            data = instruction_packet.to_string()
            nbytes = self._serial.write(data)
            if len(data) != nbytes:
                raise HkxCommunicationError(self,
                                            'instruction packet not entirely sent',
                                            instruction_packet)

            if not wait_for_status_packet:
                return

            status_packet = self.__real_read(instruction_packet, _force_lock=True)
            logger.debug('Receiving %s', status_packet,
                         extra={'port': self.port,
                                'baudrate': self.baudrate,
                                'timeout': self.timeout})

            return status_packet

    def __real_read(self, instruction_packet, _force_lock):
        with self.__force_lock(_force_lock) or self._serial_lock:
            t0 = time.time()
            data = self._serial.read(HkxPacketHeader.length)
            theader = time.time()
            headertime = theader - t0
            if not data:
                raise HkxTimeoutError(self, instruction_packet, instruction_packet.id)

            try:
                header = HkxPacketHeader.from_string(data)
                data += self._serial.read(header.packet_length-4)
                tdata = time.time()
                datatime = tdata - theader
                status_packet = HkxStatusPacket.from_string(data)

            except ValueError:
                msg = 'could not parse received data {}'.format(bytearray(data))
                raise HkxCommunicationError(self, msg, instruction_packet)

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

        except HkxTimeoutError as e:
            error_handler.handle_timeout(e)

        except HkxCommunicationError as e:
            error_handler.handle_communication_error(e)


# MARK: - Hkx Errors
class HkxError(Exception):
    """ Base class for all errors encountered using :class:`~pypot.herkulex.io.HkxIO`. """
    pass


class HkxCommunicationError(HkxError):
    """ Base error for communication error encountered when using :class:`~pypot.herkulex.io.HkxlIO`. """
    def __init__(self, hkx_io, message, instruction_packet):
        self.hkx_io = hkx_io
        self.message = message
        self.instruction_packet = instruction_packet

    def __str__(self):
        return '{self.message} after sending {self.instruction_packet}'.format(self=self)


class HkxTimeoutError(HkxCommunicationError):
    """ Timeout error encountered when using :class:`~pypot.herkulex.io.HkxIO`. """
    def __init__(self, hkx_io, instruction_packet, ids):
        HkxCommunicationError.__init__(self, hkx_io, 'timeout occured', instruction_packet)
        self.ids = ids

    def __str__(self):
        return 'motors {} did not respond after sending {}'.format(self.ids, self.instruction_packet)

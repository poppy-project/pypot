# -*- coding: utf-8 -*-

import serial
import logging
import operator
import itertools
import threading

from collections import namedtuple, OrderedDict
from contextlib import contextmanager

from ..robot.io import AbstractIO
from .conversion import *
from .packet import *


logger = logging.getLogger(__name__)
# With this logger you should always provide as extra:
# - the port
# - the baudrate
# - the timeout


_DxlControl = namedtuple('_DxlControl', ('name',
                                         'address', 'length', 'nb_elem',
                                         'access',
                                         'models',
                                         'dxl_to_si', 'si_to_dxl',
                                         'getter_name', 'setter_name'))


class _DxlAccess(object):
    readonly, writeonly, readwrite = range(3)


class DxlIO(AbstractIO):
    """ Low-level class to handle the serial communication with the robotis motors. """

    __used_ports = set()
    __controls = []

    # MARK: - Open, Close and Flush the communication

    def __init__(self,
                 port, baudrate=1000000, timeout=0.05,
                 use_sync_read=False,
                 error_handler_cls=None,
                 convert=True):
        """ At instanciation, it opens the serial port and sets the communication parameters.

            :param string port: the serial port to use (e.g. Unix (/dev/tty...), Windows (COM...)).
            :param int baudrate: default for new motors: 57600, for PyPot motors: 1000000
            :param float timeout: read timeout in seconds
            :param bool use_sync_read: whether or not to use the SYNC_READ instruction
            :param error_handler: set a handler that will receive the different errors
            :type error_handler: :py:class:`~pypot.dynamixel.error.DxlErrorHandler`
            :param bool convert: whether or not convert values to units expressed in the standard system

            :raises: :py:exc:`~pypot.dynamixel.io.DxlError` if the port is already used.

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
        return ('<DXL IO: closed={self.closed}, '
                'port="{self.port}", '
                'baudrate={self.baudrate}, '
                'timeout={self.timeout}>').format(self=self)

    def open(self, port, baudrate=1000000, timeout=0.05):
        """ Opens a new serial communication (closes the previous communication if needed).

            :raises: :py:exc:`~pypot.dynamixel.io.DxlError` if the port is already used.

            """
        self._open(port, baudrate, timeout)
        logger.info("Opening port '%s'", self.port,
                    extra={'port': port,
                           'baudrate': baudrate,
                           'timeout': timeout})

    def _open(self, port, baudrate, timeout, max_recursion=500):
        # Tries to connect to port until it succeeds to ping any motor on the bus.
        # This is  used to circumvent a bug with the driver for the USB2AX on Mac.
        # Warning: If no motor is connected on the bus, this will run forever!!!
        import platform
        # import time
        import pypot.utils.pypot_time as time

        for i in range(max_recursion):
            self._known_models.clear()
            self._known_mode.clear()

            with self._serial_lock:
                self.close(_force_lock=True)

                if port in self.__used_ports:
                    raise DxlError('port already used {}'.format(port))

                # Dirty walkaround to fix a strange bug.
                # Observed with the USB2AX on Linux with pyserial 2.7
                # We have to first open/close the port in order to make it work
                # at 1Mbauds
                if platform.system() == 'Linux' and self._sync_read:
                    self._serial = serial.Serial(port, 9600)
                    self._serial.close()

                self._serial = serial.Serial(port, baudrate, timeout=timeout)
                self.__used_ports.add(port)

            if platform.system() == 'Darwin' and self._sync_read:
                if not self.ping(DxlBroadcast):
                    self.close()
                    continue
                else:
                    time.sleep(self.timeout)
                    self.flush()
            break
        else:
            raise DxlError('could not connect to the port {}'.format(self.port))

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
            raise DxlError('attempt to flush a closed serial communication')

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
        """ Port used by the :class:`~pypot.dynamixel.io.DxlIO`. If set, will re-open a new connection. """
        return self._serial.port

    @port.setter
    def port(self, value):
        self.open(value, self.baudrate, self.timeout)

    @property
    def baudrate(self):
        """ Baudrate used by the :class:`~pypot.dynamixel.io.DxlIO`. If set, will re-open a new connection. """
        return self._serial.baudrate

    @baudrate.setter
    def baudrate(self, value):
        self.open(self.port, value, self.timeout)

    @property
    def timeout(self):
        """ Timeout used by the :class:`~pypot.dynamixel.io.DxlIO`. If set, will re-open a new connection. """
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
        pp = DxlPingPacket(id)

        try:
            self._send_packet(pp, error_handler=None)
            return True
        except DxlTimeoutError:
            return False

    def scan(self, ids=xrange(254)):
        """ Pings all ids within the specified list, by default it finds all the motors connected to the bus. """
        return [id for id in ids if self.ping(id)]

    # MARK: - Specific Getter / Setter

    def get_model(self, ids):
        """ Gets the model for the specified motors. """
        to_get_ids = [i for i in ids if i not in self._known_models]
        models = [dxl_to_model(m) for m in self._get_model(to_get_ids, convert=False)]
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

        for motor_id in baudrate_for_ids:
            if motor_id in self._known_models:
                del self._known_models[motor_id]
            if motor_id in self._known_mode:
                del self._known_mode[motor_id]

    def get_status_return_level(self, ids, **kwargs):
        """ Gets the status level for the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        srl = []
        for id in ids:
            try:
                srl.extend(self._get_status_return_level((id, ),
                           error_handler=None, convert=convert))
            except DxlTimeoutError as e:
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
        """ Sets status return level to the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        if convert:
            srl_for_id = dict(zip(srl_for_id.keys(),
                              [('never', 'read', 'always').index(s) for s in srl_for_id.values()]))
        self._set_status_return_level(srl_for_id, convert=False)

    def get_mode(self, ids):
        """ Gets the mode ('joint' or 'wheel') for the specified motors. """
        to_get_ids = [id for id in ids if id not in self._known_mode]
        limits = self.get_angle_limit(to_get_ids, convert=False)
        modes = ('wheel' if limit == (0, 0) else 'joint' for limit in limits)

        self._known_mode.update(zip(to_get_ids, modes))

        return tuple(self._known_mode[id] for id in ids)

    def set_wheel_mode(self, ids):
        """ Sets the specified motors to wheel mode. """
        self._set_mode(dict(zip(ids, itertools.repeat('wheel'))))

    def set_joint_mode(self, ids):
        """ Sets the specified motors to joint mode. """
        self._set_mode(dict(zip(ids, itertools.repeat('joint'))))

    def _set_mode(self, mode_for_id):
        models = ['MX' if m.startswith('MX') else '*' for m in self.get_model(list(mode_for_id.keys()))]
        pos_max = [position_range[m][0] for m in models]
        limits = ((0, 0) if mode == 'wheel' else (0, pos_max[i] - 1)
                  for i, mode in enumerate(mode_for_id.itervalues()))

        self._set_angle_limit(dict(zip(mode_for_id.keys(), limits)), convert=False)
        self._known_mode.update(mode_for_id.items())

    def set_angle_limit(self, limit_for_id, **kwargs):
        """ Sets the angle limit to the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert

        if 'wheel' in self.get_mode(limit_for_id.keys()):
            raise ValueError('can not change the angle limit of a motor in wheel mode')

        if (0, 0) in limit_for_id.values():
            raise ValueError('can not set limit to (0, 0)')

        self._set_angle_limit(limit_for_id, convert=convert)

    def switch_led_on(self, ids):
        """ Switches on the LED of the motors with the specified ids. """
        self._set_LED(dict(zip(ids, itertools.repeat(True))))

    def switch_led_off(self, ids):
        """ Switches off the LED of the motors with the specified ids. """
        self._set_LED(dict(zip(ids, itertools.repeat(False))))

    def enable_torque(self, ids):
        """ Enables torque of the motors with the specified ids. """
        self._set_torque_enable(dict(zip(ids, itertools.repeat(True))))

    def disable_torque(self, ids):
        """ Disables torque of the motors with the specified ids. """
        self._set_torque_enable(dict(zip(ids, itertools.repeat(False))))

    def get_pid_gain(self, ids, **kwargs):
        """ Gets the pid gain for the specified motors. """
        return tuple([tuple(reversed(t)) for t in self._get_pid_gain(ids, **kwargs)])

    def set_pid_gain(self, pid_for_id, **kwargs):
        """ Sets the pid gain to the specified motors. """
        pid_for_id = dict(itertools.izip(pid_for_id.iterkeys(),
                                         [tuple(reversed(t)) for t in pid_for_id.values()]))
        self._set_pid_gain(pid_for_id, **kwargs)

    # MARK: - Generic Getter / Setter

    def get_control_table(self, ids, **kwargs):
        """ Gets the full control table for the specified motors.

            ..note:: This function requires the model for each motor to be known. Querring this additional information might add some extra delay.

            """
        error_handler = kwargs['error_handler'] if ('error_handler' in kwargs) else self._error_handler
        convert = kwargs['convert'] if ('convert' in kwargs) else self._convert

        bl = ('goal position speed load', 'present position speed load')
        controls = [c for c in self._DxlIO__controls if c.name not in bl]

        res = []

        for id, model in zip(ids, self.get_model(ids)):
            controls = [c for c in controls if model in c.models]

            controls = sorted(controls, key=lambda c: c.address)

            address = controls[0].address
            length = controls[-1].address + controls[-1].nb_elem * controls[-1].length

            rp = DxlReadDataPacket(id, address, length)
            sp = self._send_packet(rp, error_handler=error_handler)

            d = OrderedDict()
            for c in controls:
                v = dxl_decode_all(sp.parameters[c.address:c.address + c.nb_elem * c.length], c.nb_elem)
                d[c.name] = c.dxl_to_si(v, model) if convert else v

            res.append(d)

        return tuple(res)

    @classmethod
    def _generate_accessors(cls, control):
        cls.__controls.append(control)

        if control.access in (_DxlAccess.readonly, _DxlAccess.readwrite):
            def my_getter(self, ids, **kwargs):
                return self._get_control_value(control, ids, **kwargs)

            func_name = control.getter_name if control.getter_name else 'get_{}'.format(control.name.replace(' ', '_'))
            func_name = '_{}'.format(func_name) if hasattr(cls, func_name) else func_name
            my_getter.__doc__ = 'Gets {} from the specified motors.'.format(control.name)
            my_getter.__name__ = func_name
            setattr(cls, func_name, my_getter)

        if control.access in (_DxlAccess.writeonly, _DxlAccess.readwrite):
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

        if self._sync_read and len(ids) > 1:
            rp = DxlSyncReadPacket(ids, control.address, control.length * control.nb_elem)
            sp = self._send_packet(rp, error_handler=error_handler)

            if not sp:
                return ()

            values = sp.parameters

        else:
            values = []
            for motor_id in ids:
                rp = DxlReadDataPacket(motor_id, control.address, control.length * control.nb_elem)
                sp = self._send_packet(rp, error_handler=error_handler)

                if not sp:
                    return ()

                values.extend(sp.parameters)

        values = list(itertools.izip(*([iter(values)] * control.length * control.nb_elem)))
        values = [dxl_decode_all(value, control.nb_elem) for value in values]

        if not values:
            return ()

        # when using SYNC_READ instead of getting a timeout
        # a non existing motor will "return" the maximum value
        if self._sync_read:
            max_val = 2 ** (8 * control.length) - 1
            if max_val in (itertools.chain(*values) if control.nb_elem > 1 else values):
                lost_ids = []
                for i, v in enumerate(itertools.chain(*values) if control.nb_elem > 1 else values):
                    if v == max_val:
                        lost_ids.append(ids[i // control.nb_elem])
                e = DxlTimeoutError(self, rp, list(set(lost_ids)))
                if self._error_handler:
                    self._error_handler.handle_timeout(e)
                    return ()
                else:
                    raise e

        if convert:
            models = self.get_model(ids)
            if not models:
                return ()
            values = [control.dxl_to_si(v, m) for v, m in zip(values, models)]

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
                                    map(control.si_to_dxl, value_for_id.values(), models)))

        data = []
        for motor_id, value in value_for_id.iteritems():
            data.extend(itertools.chain((motor_id, ),
                                        dxl_code_all(value, control.length, control.nb_elem)))

        wp = DxlSyncWritePacket(control.address, control.length * control.nb_elem, data)
        self._send_packet(wp, wait_for_status_packet=False)

    # MARK: - Send/Receive packet
    def __real_send(self, instruction_packet, wait_for_status_packet, _force_lock):
        if self.closed:
            raise DxlError('try to send a packet on a closed serial communication')

        logger.debug('Sending %s', instruction_packet,
                     extra={'port': self.port,
                            'baudrate': self.baudrate,
                            'timeout': self.timeout})

        with self.__force_lock(_force_lock) or self._serial_lock:
            self.flush(_force_lock=True)

            data = instruction_packet.to_string()
            nbytes = self._serial.write(data)
            if len(data) != nbytes:
                raise DxlCommunicationError(self,
                                            'instruction packet not entirely sent',
                                            instruction_packet)

            if not wait_for_status_packet:
                return

            data = self._serial.read(DxlPacketHeader.length)
            if not data:
                raise DxlTimeoutError(self, instruction_packet, instruction_packet.id)

            try:
                header = DxlPacketHeader.from_string(data)
                data += self._serial.read(header.packet_length)
                status_packet = DxlStatusPacket.from_string(data)

            except ValueError:
                msg = 'could not parse received data {}'.format(bytearray(data))
                raise DxlCommunicationError(self, msg, instruction_packet)

            logger.debug('Receiving %s', status_packet,
                         extra={'port': self.port,
                                'baudrate': self.baudrate,
                                'timeout': self.timeout})

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

        except DxlTimeoutError as e:
            error_handler.handle_timeout(e)

        except DxlCommunicationError as e:
            error_handler.handle_communication_error(e)


# MARK: - Dxl Errors
class DxlError(Exception):
    """ Base class for all errors encountered using :class:`~pypot.dynamixel.io.DxlIO`. """
    pass


class DxlCommunicationError(DxlError):
    """ Base error for communication error encountered when using :class:`~pypot.dynamixel.io.DxlIO`. """
    def __init__(self, dxl_io, message, instruction_packet):
        self.dxl_io = dxl_io
        self.message = message
        self.instruction_packet = instruction_packet

    def __str__(self):
        return '{self.message} after sending {self.instruction_packet}'.format(self=self)


class DxlTimeoutError(DxlCommunicationError):
    """ Timeout error encountered when using :class:`~pypot.dynamixel.io.DxlIO`. """
    def __init__(self, dxl_io, instruction_packet, ids):
        DxlCommunicationError.__init__(self, dxl_io, 'timeout occured', instruction_packet)
        self.ids = ids

    def __str__(self):
        return 'motors {} did not respond after sending {}'.format(self.ids, self.instruction_packet)

# MARK: - Generate the accessors


def _add_control(name,
                 address, length=2, nb_elem=1,
                 access=_DxlAccess.readwrite,
                 models=set(dynamixelModels.values()),
                 dxl_to_si=lambda val, model: val,
                 si_to_dxl=lambda val, model: val,
                 getter_name=None,
                 setter_name=None):

    control = _DxlControl(name,
                          address, length, nb_elem,
                          access,
                          models,
                          dxl_to_si, si_to_dxl,
                          getter_name, setter_name)

    DxlIO._generate_accessors(control)


_add_control('model',
             address=0x00,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_model)

_add_control('firmware',
             address=0x02, length=1,
             access=_DxlAccess.readonly)

_add_control('id',
             address=0x03, length=1,
             access=_DxlAccess.writeonly,
             setter_name='change_id')

_add_control('baudrate',
             address=0x04, length=1,
             access=_DxlAccess.writeonly,
             setter_name='change_baudrate',
             si_to_dxl=baudrate_to_dxl)

_add_control('return delay time',
             address=0x05, length=1,
             dxl_to_si=dxl_to_rdt,
             si_to_dxl=rdt_to_dxl)

_add_control('angle limit',
             address=0x06, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_degree(value[1], model)),
             si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                             degree_to_dxl(value[1], model)))

_add_control('drive mode',
             address=0x0A, length=1,
             access=_DxlAccess.readwrite,
             models=('MX-106', ),
             dxl_to_si=dxl_to_drive_mode,
             si_to_dxl=drive_mode_to_dxl)

_add_control('highest temperature limit',
             address=0x0B, length=1,
             dxl_to_si=dxl_to_temperature,
             si_to_dxl=temperature_to_dxl)

_add_control('voltage limit',
             address=0x0C, length=1, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_voltage(value[0], model),
                                             dxl_to_voltage(value[1], model)),
             si_to_dxl=lambda value, model: (voltage_to_dxl(value[0], model),
                                             voltage_to_dxl(value[1], model)))

_add_control('max torque',
             address=0x0E,
             dxl_to_si=dxl_to_torque,
             si_to_dxl=torque_to_dxl)

_add_control('status return level',
             address=0x10, length=1,
             dxl_to_si=dxl_to_status,
             si_to_dxl=status_to_dxl)

_add_control('alarm LED',
             address=0x11, length=1,
             dxl_to_si=dxl_to_alarm,
             si_to_dxl=alarm_to_dxl)

_add_control('alarm shutdown',
             address=0x12, length=1,
             dxl_to_si=dxl_to_alarm,
             si_to_dxl=alarm_to_dxl)

_add_control('torque_enable',
             address=0x18, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl,
             getter_name='is_torque_enabled',
             setter_name='_set_torque_enable')

_add_control('LED',
             address=0x19, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl,
             setter_name='_set_LED',
             getter_name='is_led_on')

_add_control('pid gain',
             address=0x1A, length=1, nb_elem=3,
             models=('MX-12', 'MX-28', 'MX-64', 'MX-106'),
             dxl_to_si=dxl_to_pid,
             si_to_dxl=pid_to_dxl)

_add_control('compliance margin',
             address=0x1A, length=1, nb_elem=2,
             models=('AX-12', 'AX-18', 'RX-28', 'RX-64'))

_add_control('compliance slope',
             address=0x1C, length=1, nb_elem=2,
             models=('AX-12', 'AX-18', 'RX-28', 'RX-64'))

_add_control('goal position',
             address=0x1E,
             dxl_to_si=dxl_to_degree,
             si_to_dxl=degree_to_dxl)

_add_control('moving speed',
             address=0x20,
             dxl_to_si=dxl_to_speed,
             si_to_dxl=speed_to_dxl)

_add_control('torque limit',
             address=0x22,
             dxl_to_si=dxl_to_torque,
             si_to_dxl=torque_to_dxl)

_add_control('goal position speed load',
             address=0x1E, nb_elem=3,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_speed(value[1], model),
                                             dxl_to_load(value[2], model)),
             si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                             speed_to_dxl(value[1], model),
                                             torque_to_dxl(value[2], model)))

_add_control('present position',
             address=0x24,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_degree)

_add_control('present speed',
             address=0x26,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_speed)

_add_control('present load',
             address=0x28,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_load)

_add_control('present position speed load',
             address=0x24, nb_elem=3,
             access=_DxlAccess.readonly,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_speed(value[1], model),
                                             dxl_to_load(value[2], model)))

_add_control('present voltage',
             address=0x2A, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_voltage)

_add_control('present temperature',
             address=0x2B, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_temperature)

_add_control('moving',
             address=0x2E, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_bool,
             getter_name='is_moving')

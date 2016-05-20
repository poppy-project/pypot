# -*- coding: utf-8 -*-

import serial
import logging
import operator
import itertools
import threading

from collections import namedtuple, OrderedDict
from contextlib import contextmanager

from ..conversion import (dxl_code_all, dxl_decode_all, decode_error,
                          dxl_to_model)


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


class AbstractDxlIO(object):
    """ Low-level class to handle the serial communication with the robotis motors. """

    __used_ports = set()
    __controls = []
    _protocol = None

    @classmethod
    def get_used_ports(cls):
        return list(cls.__used_ports)

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
                    raise DxlError('Another instance of pypot use the port {}. You should restart your Python kernel to pass through this issue.'.format(port))

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
                if not self.ping(self._protocol.DxlBroadcast):
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
        pp = self._protocol.DxlPingPacket(id)

        try:
            self._send_packet(pp, error_handler=None)
            return True
        except DxlTimeoutError:
            return False

    def scan(self, ids=range(254)):
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
        controls = [c for c in self._AbstractDxlIO__controls if c.name not in bl]

        res = []

        for id, model in zip(ids, self.get_model(ids)):
            controls = [c for c in controls if model in c.models]

            controls = sorted(controls, key=lambda c: c.address)

            address = controls[0].address
            length = controls[-1].address + controls[-1].nb_elem * controls[-1].length

            rp = self._protocol.DxlReadDataPacket(id, address, length)
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
            rp = self._protocol.DxlSyncReadPacket(ids, control.address,
                                                  control.length * control.nb_elem)

            with self._serial_lock:
                sp = self._send_packet(rp,
                                       error_handler=error_handler,
                                       _force_lock=True)
                if not sp:
                    return ()

                if self._protocol.name == 'v1':
                    values = sp.parameters

                elif self._protocol.name == 'v2':
                    values = list(sp.parameters)
                    for i in range(len(ids) - 1):
                        try:
                            sp = self.__real_read(rp, _force_lock=True)
                        except (DxlTimeoutError, DxlCommunicationError):
                            return ()
                        values.extend(sp.parameters)

                    if len(values) < len(ids):
                        return ()

        else:
            values = []
            for motor_id in ids:
                rp = self._protocol.DxlReadDataPacket(motor_id, control.address, control.length * control.nb_elem)
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
        if self._sync_read and self._protocol.name == 'v1':
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

        wp = self._protocol.DxlSyncWritePacket(control.address, control.length * control.nb_elem, data)
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

            status_packet = self.__real_read(instruction_packet, _force_lock=True)

            logger.debug('Receiving %s', status_packet,
                         extra={'port': self.port,
                                'baudrate': self.baudrate,
                                'timeout': self.timeout})

            return status_packet

    def __real_read(self, instruction_packet, _force_lock):
        with self.__force_lock(_force_lock) or self._serial_lock:
            data = self._serial.read(self._protocol.DxlPacketHeader.length)
            if not data:
                raise DxlTimeoutError(self, instruction_packet, instruction_packet.id)

            try:
                header = self._protocol.DxlPacketHeader.from_string(data)
                data += self._serial.read(header.packet_length)
                status_packet = self._protocol.DxlStatusPacket.from_string(data)

            except ValueError:
                msg = 'could not parse received data {}'.format(bytearray(data))
                raise DxlCommunicationError(self, msg, instruction_packet)

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


@contextmanager
def with_True():
    yield True

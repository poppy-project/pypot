import sys
import platform
import glob
import logging

import serial.tools.list_ports


from .io import DxlIO, Dxl320IO, DxlError
from .error import BaseErrorHandler
from .syncloop import BaseDxlController
from .motor import DxlMXMotor, DxlAXRXMotor, DxlXL320Motor

from ..robot import Robot

logger = logging.getLogger(__name__)


def _get_available_ports():
    """ Tries to find the available serial ports on your system. """
    if platform.system() == 'Darwin':
        return glob.glob('/dev/tty.usb*')

    elif platform.system() == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyAMA*')

    elif sys.platform.lower() == 'cygwin':
        return glob.glob('/dev/com*')

    elif platform.system() == 'Windows':
        import _winreg
        import itertools

        ports = []
        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)

        for i in itertools.count():
            try:
                ports.append(str(_winreg.EnumValue(key, i)[1]))
            except WindowsError:
                return ports
    else:
        raise EnvironmentError('{} is an unsupported platform, cannot find serial ports !'.format(platform.system()))
    return []


def get_available_ports(only_free=False):
    ports = _get_available_ports()

    if only_free:
        ports = list(set(ports) - set(DxlIO.get_used_ports()))

    return ports


def get_port_vendor_info(port=None):
    """ Return vendor informations of a usb2serial device.
        It may depends on the Operating System.
        :param string port: port of the usb2serial device

        :Example:

        Result with a USB2Dynamixel on Linux:
        In [1]: import pypot.dynamixel
        In [2]: pypot.dynamixel.get_port_vendor_info('/dev/ttyUSB0')
        Out[2]: 'USB VID:PID=0403:6001 SNR=A7005LKE' """

    port_info_dict = dict((x[0], x[2]) for x in serial.tools.list_ports.comports())
    return port_info_dict[port] if port is not None else port_info_dict


def find_port(ids, strict=True):
    """ Find the port with the specified attached motor ids.

        :param list ids: list of motor ids to find
        :param bool strict: specify if all ids should be find (when set to False, only half motor must be found)

        .. warning:: If two (or more) ports are attached to the same list of motor ids the first match will be returned.

    """
    ids_founds = []
    for port in get_available_ports():
        for DxlIOCls in (DxlIO, Dxl320IO):
            try:
                with DxlIOCls(port) as dxl:
                    _ids_founds = dxl.scan(ids)
                    ids_founds += _ids_founds

                    if strict and len(_ids_founds) == len(ids):
                        return port

                    if not strict and len(_ids_founds) >= len(ids) / 2:
                        logger.warning('Missing ids: {}'.format(ids, list(set(ids) - set(_ids_founds))))
                        return port

                    if len(ids_founds) > 0:
                        logger.warning('Port:{} ids found:{}'.format(port, _ids_founds))

            except DxlError:
                logger.warning('DxlError on port {}'.format(port))
                continue

    raise IndexError('No suitable port found for ids {}. These ids are missing {} !'.format(
        ids, list(set(ids) - set(ids_founds))))


def autodetect_robot():
    """ Creates a :class:`~pypot.robot.robot.Robot` by detecting dynamixel motors on all available ports. """
    motor_controllers = []

    for port in get_available_ports():
        for DxlIOCls in (DxlIO, Dxl320IO):
            dxl_io = DxlIOCls(port)
            ids = dxl_io.scan()

            if not ids:
                dxl_io.close()
                continue

            models = dxl_io.get_model(ids)

            motorcls = {
                'MX': DxlMXMotor,
                'RX': DxlAXRXMotor,
                'AX': DxlAXRXMotor,
                'XL': DxlXL320Motor
            }

            motors = [motorcls[model[:2]](id, model=model)
                      for id, model in zip(ids, models)]

            c = BaseDxlController(dxl_io, motors)
            motor_controllers.append(c)

    return Robot(motor_controllers)

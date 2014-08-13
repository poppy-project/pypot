import platform
import glob

from .io import DxlIO, DxlError
from .error import BaseErrorHandler
from .controller import BaseDxlController
from .motor import DxlMXMotor, DxlAXRXMotor

from ..robot import Robot


def get_available_ports():
    """ Tries to find the available usb2serial port on your system. """
    if platform.system() == 'Darwin':
        return glob.glob('/dev/tty.usb*')

    elif platform.system() == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

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

    return []


def find_port(ids, strict=True):
    """ Find the port with the specified attached motor ids.

        :param list ids: list of motor ids to find
        :param bool strict: specify if all ids should be find (when set to False, only half motor must be found)

        .. warning:: If two (or more) ports are attached to the same list of motor ids the first match will be returned.

    """
    for port in get_available_ports():
        try:
            with DxlIO(port) as dxl:
                founds = len(dxl.scan(ids))

                if strict and founds == len(ids):
                    return port

                if not strict and founds >= len(ids) / 2:
                    return port
        except DxlError:
            continue

    raise IndexError('No suitable port found for ids {}!'.format(ids))


def autodetect_robot():
    """ Creates a :class:`~pypot.robot.robot.Robot` by detecting dynamixel motors on all available ports. """
    motor_controllers = []

    for port in get_available_ports():
        dxl_io = DxlIO(port)
        ids = dxl_io.scan()
        models = dxl_io.get_model(ids)
        motors = [(DxlMXMotor(id, model=model) if model.startswith('MX')
                   else DxlAXRXMotor(id, model=model))
                  for id, model in zip(ids, models)]

        c = BaseDxlController(dxl_io, motors)
        motor_controllers.append(c)

    return Robot(motor_controllers)

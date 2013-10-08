import platform
import glob

from pypot.dynamixel.io import DxlIO
from pypot.dynamixel.controller import DxlController
from pypot.dynamixel.error import BaseErrorHandler


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
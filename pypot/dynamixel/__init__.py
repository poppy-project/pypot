import platform
import numpy
import glob

from pypot.dynamixel.io import DxlIO, DxlTimeoutError
from pypot.dynamixel.motor import DxlMotor
from pypot.dynamixel.controller import DxlController
from pypot.dynamixel.error import BaseErrorHandler

def get_available_ports():
    """ Tries to find the available port (only works for Mac and Linux). """
    if platform.system() == 'Darwin':
        return glob.glob('/dev/tty.usb*')

    elif platform.system() == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    return []
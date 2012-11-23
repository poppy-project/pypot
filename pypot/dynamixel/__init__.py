import platform
import numpy
import glob

from pypot.dynamixel.io import DynamixelIO



def get_available_ports():
    """ Tries to find the available port (only works for Mac and Linux). """
    if platform.system() == 'Darwin':
        return glob.glob('/dev/tty.usb*')

    elif platform.system() == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    return []
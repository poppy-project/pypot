
from io import DynamixelIO

import os
import glob

def get_available_ports():
    op_system = os.uname()[0]
    
    if op_system == 'Darwin':
        return glob.glob('/dev/tty.usb*')
    
    elif op_system == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    raise NotImplementedError('Unknown operating system')

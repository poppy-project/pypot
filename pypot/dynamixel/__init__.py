import os
import glob


from pypot.dynamixel.io import DynamixelIO
from pypot.dynamixel.motor import DynamixelMotor
from pypot.dynamixel.controller import DynamixelController



def get_available_ports():
    # TODO: windows ?
    """
        """
    op_system = os.uname()[0]
    
    if op_system == 'Darwin':
        return glob.glob('/dev/tty.usb*')
    
    elif op_system == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    raise NotImplementedError('Unknown operating system')

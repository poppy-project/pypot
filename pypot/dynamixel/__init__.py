import os
import glob


from pypot.dynamixel.io import DynamixelIO
from pypot.dynamixel.motor import DynamixelMotor
from pypot.dynamixel.controller import DynamixelController



def get_available_ports():
    """ 
        Returns the available ports found.
        
        The available ports are looked for in the following path depending on the OS:
            * Linux : /dev/ttyACM* and /dev/ttyUSB*
            * Mac OS : /dev/tty.usb*
        
        :raises: :py:exc:`NotImplementedError` if your OS is not one of the currently supported (Linux, Mac OS).
        
    """
    # TODO: windows ?

    op_system = os.uname()[0]
    
    if op_system == 'Darwin':
        return glob.glob('/dev/tty.usb*')
    
    elif op_system == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    raise NotImplementedError('Unknown operating system: %s' % (op_system))

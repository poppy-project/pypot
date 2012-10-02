import os
import glob

from pypot.dynamixel.io import DynamixelIO
from pypot.dynamixel.motor import _DynamixelMotor, DynamixelMotor
from pypot.dynamixel.controller import DynamixelController


for name in ('angle_limits', 'current_position', 'temperature', 'load', 'max_torque'):
    _DynamixelMotor._generate_read_accessor(name)

for name in ('goal_position', 'mode', 'speed', 'torque_limit'):
    _DynamixelMotor._generate_write_accessor(name)

def get_available_ports():
    """
        Returns the available ports found.
        
        The available ports are looked for in the following path depending on the OS:
            * Linux : /dev/ttyACM* and /dev/ttyUSB*
            * Mac OS : /dev/tty.usb*
        
        :raises: :py:exc:`NotImplementedError` if your OS is not one of the currently supported (Linux, Mac OS).
        
    """

    import platform
    s = platform.system()
    
    try:
        import serial.tools.list_ports

        if s == 'Linux':
            return serial.tools.list_ports.glob.glob('/dev/ttyACM*') + \
                    serial.tools.list_ports.glob.glob('/dev/ttyUSB*')
        
        elif s == 'Darwin':
            return serial.tools.list_ports.glob.glob('/dev/tty.usbserial-*')

        elif s == 'Windows':
            return serial.tools.list_ports.grep('COM*')
            
    except ImportError:
        if s == 'Darwin':
            return glob.glob('/dev/tty.usb*')
    
        elif s == 'Linux':
            return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')


    raise NotImplementedError('Unknown operating system: %s' % (s))

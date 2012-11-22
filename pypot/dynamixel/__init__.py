import numpy
import glob
import platform


from pypot.dynamixel.io import DynamixelIO



if platform.system() == 'Darwin':
    def safe_connect(port, baudrate=1000000, timeout=0.05,
                     max_trials=numpy.inf):
        """ Tries to connect to port until it succeeds to ping any motor on the bus.

            .. note:: This is only used to circumvent a bug with the driver for the USB2AX on Mac.
            
            """
        trials = 1

        while trials <= max_trials:
            dxl_io = DynamixelIO(port, baudrate, timeout)

            if dxl_io.ping_any():
                return dxl_io

            dxl_io.close()
            trials += 1


def get_available_ports():
    """ Tries to find the available port (only works for Mac and Linux). """
    if platform.system() == 'Darwin':
        return glob.glob('/dev/tty.usb*')

    elif platform.system() == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    return []
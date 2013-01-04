.. _dynamixel:

Communication with the dynamixel motors
=======================================

.. automodule:: pypot.dynamixel

This package handles the communication with dynamixel motors from robotis. Using a USB communication device such as USB2DYNAMIXEL or USB2AX, you can open serial communication with robotis motors (MX, RX, AX) using communication protocols TTL or RS485. More specifically, it allows easy access (both reading and writing) to the different registers of any dynamixel motors. Those registers includes values such as position, speed or torque. The whole list of registers can directly be found on the robotis website http://support.robotis.com/en/product/dxl_main.htm).
    
You can access the register of the motors through two different ways:
    
* In the first case, you can get or set a value to a motor by directly sending a request and waiting for the motor to answer. Here, you only use the low level API to communicate with the motor (refer to section :ref:`lowlevel` for more details).

* In the second case, you define requests which will automatically be sent at a predefined frequency. The values obtained from the requests are stored in a local copy that you can freely access at any time. However, you can only access the last synchronized value. This second method encapsulate the first approach to prevent you from writing repetitive request (refer to section :ref:`controller` for further details).
    
While the second approach allows the writing of simpler code without detailed knowledge of how the communication with robotis motor works, the first approach may allow for more performance through fine tuning of the communication needed in  particular applications and is also more suited when no synchronization loop is needed. Examples of both approaches will be provided in their respective section.
    
This package also provides a convenient function to automatically detect the available usb2serial ports which can be used to communicate with robotis motors.

.. autofunction:: pypot.dynamixel.get_available_ports


.. _lowlevel:

Low-level IO API
----------------

.. automodule:: pypot.dynamixel.io 

The low-level API almost directly encapsulate the communication protocol used by dynamixel motors. This protocol can be used to access any register of these motors. The :py:class:`pypot.dynamixel.DxlIO` class is used to handle the communication with a particular port.

.. note:: The port can only be accessed by a single DxlIO instance.

More precisely, this class can be used to:

* open/close the communication
* discover motors (ping or scan)
* access the different control (read and write)


As an example, you can write::

    with DxlIO('/dev/USB0') as dxl_io:
        ids = dxl_io.scan([1, 2, 3, 4, 5])
        
        for id in ids:
            print 'pos of motor', id, ':', dxl_io.get_present_position(id)
            
        dxl_io.set_goal_position(dict(itertools.izip(ids, 
                                                     itertools.repeat(0))))

.. note:: As shown in the example above, this class can be used as a context manager.

The communication is thread-safe to avoid collision in the communication buses.


.. autoclass:: pypot.dynamixel.DxlIO
    :members:
    
.. autoexception:: pypot.dynamixel.io.DxlError
    
    
.. _controller:

Dynamixel Controller
--------------------

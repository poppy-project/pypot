.. _tutorial:

Tutorial
********

Communication with robotis motors
=================================

PyPot handles the communication with dynamixel motors from robotis. Using a USB communication device such as USB2DYNAMIXEL or USB2AX, you can open serial communication with robotis motors (MX, RX, AX) using communication protocols TTL or RS485. More specifically, it allows easy access (both reading and writing) to the different registers of any dynamixel motors. Those registers includes values such as position, speed or torque. The whole list of registers can directly be found on the robotis website http://support.robotis.com/en/product/dxl_main.htm.
    
You can access the register of the motors through two different ways:
    
* **Low-level API:** In the first case, you can get or set a value to a motor by directly sending a request and waiting for the motor to answer. Here, you only use the low level API to communicate with the motor (refer to section :ref:`lowlevel` for more details).

* **Controller API:** In the second case, you define requests which will automatically be sent at a predefined frequency. The values obtained from the requests are stored in a local copy that you can freely access at any time. However, you can only access the last synchronized value. This second method encapsulate the first approach to prevent you from writing repetitive request (refer to section :ref:`sync_loop` for further details).
    
While the second approach allows the writing of simpler code without detailed knowledge of how the communication with robotis motor works, the first approach may allow for more performance through fine tuning of the communication needed in  particular applications. Examples of both approaches will be provided in the next sections.


.. _lowlevel:

Low-level API
=============

The low-level API almost directly encapsulates the communication protocol used by dynamixel motors. This protocol can be used to access any register of these motors. The :py:class:`~pypot.dynamixel.io.DxlIO` class is used to handle the communication with a particular port.

.. note:: The port can only be accessed by a single DxlIO instance.

More precisely, this class can be used to:

* open/close the communication
* discover motors (ping or scan)
* access the different control (read and write)

The communication is thread-safe to avoid collision in the communication buses.


As an example, you can write::

    with DxlIO('/dev/USB0') as dxl_io:
        ids = dxl_io.scan([1, 2, 3, 4, 5])
        
        print dxl_io.get_present_position(ids)            
        dxl_io.set_goal_position(dict(zip(ids, itertools.repeat(0))))

.. _open_connection:

Opening/Closing a communication port
------------------------------------

In order to open a connection with the device, you will need to know what port it is connected to. PyPot has a function named :func:`~pypot.dynamixel.get_available_ports` which will try to auto-discover any compatible devices connected to the communication ports. 

To create a connection, open up a python terminal and type the following code::

    import pypot.dynamixel
    
    ports = pypot.dynamixel.get_available_ports()
    
    if not ports:
        raise IOError('no port found!')

    print 'connecting on the first available port:', ports[0]
    dxl_io = pypot.dynamixel.DxlIO(ports[0])
    
This should open a connection through a virtual communication port to your device.

.. warning:: It is important to note that it will open a connection using a default baud rate. By default your motors are set up to work on the robotis default baud rate (57140) while PyPot is set up to work with a 1000000 baud rate. To communicate with your motors, you must ensure that this baud rate is the same baud rate that the motors are configure to use. So, you will need to change either the configuration of your motors (see :ref:`Herborist <herborist>` section) or change the default baudrate of your connection.

To set up a connection with another baud rate you can write::

    dxl_io = pypot.dynamixel.DxlIO(port, baudrate=57140)
    
The communication can be closed using the :meth:`~pypot.dynamixel.io.DxlIO.close` method.

.. note:: The class :class:`~pypot.dynamixel.io.DxlIO` can also be used as a `Context Manager <http://docs.python.org/2/library/contextlib.html>`_ (the :meth:`~pypot.dynamixel.io.DxlIO.close` method will automatically be called at the end). 
    For instance::
    
        with pypot.dynamixel.DxlIO('/dev/ttyUSB0') as dxl_io:
            ...

Finding motors
--------------

Pypot has been designed to work specifically with the Robotis range of motors. These motors use two different protocols to communicate: TTL (3 wire bus) and RS485 (4 wire Bus). The motors can be daisey chained together with other types of motors on the same bus *as long as the bus communicates using the same protocol*. This means that MX-28 and AX-12 can communicate on the same bus, but cannot be connected to a RX-28.

All motors work sufficiently well with a 12V supply. Some motors can use more than 12V but you must be careful not to connect an 18V supply on a bus that contains motors that can only use 12V! Connect this 12V SMPS supply (switch mode power supply) to a Robotis SMPS2Dynamixel device which regulates the voltage coming from the SMPS. Connect your controller device and a single motor to this SMPS2Dynamixel. 

Open your python terminal and create your :class:`~pypot.dynamixel.io.DxlIO` as described in the above section :ref:`open_connection`.
    
To detect the motors and find their id you can scan the bus. To avoid spending a long time searching all possible values, you can add a list of values to test::

    dxl_io.scan()
    >>> [4, 23, 24, 25]

    dxl_io.scan([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    >>> [4]
    
Or, you can use the shorthand::

    dxl_io.scan(range(10))
    >>> [4]

This should produce a list of the ids of the motors that are connected to the bus. Each motor on the bus must have a unique id. This means that unless your motors have been configured in advance, it is better to connect them one by one to ensure they all have unique ids first.


Low-level control
-----------------

Now we have the id of the motors connected, we can begin to access their functions by using their id. Try to find out the present position (in degrees) of the motor by typing the following::

    dxl_io.get_present_position((4, ))
    >>> (67.8, )
    
You can also write a goal position (in degrees) to the motor using the following::

    dxl_io.set_goal_position({4: 0})
    
The motors are handled in degrees where 0 is considered the central point of the motor turn. For the MX motors, the end points are -180° and 180°. For the AX and RX motors, these end points are -150° to 150°.

.. warning:: As you can see on the example above, you should always pass the id parameter as a list. This is intended as getting a value from several motors takes the same time as getting a value from a single motor (thanks to the SYNC_READ instruction). Similarly, we use dictionnary with pairs of (id, value) to set value to a specific register of motors and benefit from the SYNC_WRITE instruction.

As an example of what you can do with the low-level API, we are going to apply a sinusoid on two motors (make sure that the motion will not damage your robot before running the example!). Here is a complete listing of the code needed::

    import itertools
    import numpy
    import time

    import pypot.dynamixel
    
    AMP = 30
    FREQ = 0.5
    
    if __name__ == '__main__':
        ports = pypot.dynamixel.get_available_ports()
        print 'available ports:', ports
    
        if not ports:
            raise IOError('No port available.')

        port = ports[0]
        print 'Using the first on the list', port
    
        dxl_io = pypot.dynamixel.DxlIO(port)
        print 'Connected!'
    
        found_ids = dxl_io.scan()
        print 'Found ids:', found_ids
    
        if len(found_ids) < 2:
            raise IOError('You should connect at least two motors on the bus for this test.')

        ids = found_ids[:2]

        dxl_io.enable_torque(ids)

        speed = dict(zip(ids, itertools.repeat(200)))
        dxl_io.set_moving_speed(speed)
    
        pos = dict(zip(ids, itertools.repeat(0)))
        dxl_io.set_goal_position(pos)
    
    
        t0 = time.time()
        while True:
            t = time.time()
            if (t - t0) > 5:
                break
                
            pos = AMP * numpy.sin(2 * numpy.pi * FREQ * t)
            dxl_io.set_goal_position(dict(zip(ids, itertools.repeat(pos))))
            
            time.sleep(0.02)

    
    
Thanks to PyPot, you can access all registers of your motors using the same syntax (e.g. :meth:`~pypot.dynamixel.io.DxlIO.get_present_speed`, :meth:`~pypot.dynamixel.io.DxlIO.set_max_torque`, :meth:`~pypot.dynamixel.io.DxlIO.get_pid_gain`). Some shortcuts have been provided to make the code more readable (e.g. :meth:`~pypot.dynamixel.io.DxlIO.enable_torque` instead of set_torque_enabled). You can refer to the documentation of :class:`~pypot.dynamixel.io.DxlIO` for a complete list of all the available methods.



.. note:: PyPot provides an easy way to extend the code and automatically create methods to access new registers added by robotis.


Using the robot abstraction
===========================



Writing a configuration file
----------------------------

.. The configuration file contains several important features that help build both your robot and the software to manage you robot written in xml. The important features are listed below:
..     * <Robot> 
..         * <EEPROM> - This holds the basic default configuration values that are shared by all the motors such as their return delay time.
..         * <DynamixelController> - This tag holds the information pertaining to a controller and all the items connected to its bus.
..             * <AlarmBlackList> - Here we can list any alarms that we are *not* interested in receiving messages from. For example we may have our own special method of handling 'out of bounds' error messages and may not want the motors to handle this.
..             * <DynamixelMotor> - This is a description of all the custom setup values for each motor. Meta information, such as the motor access name or orientation, is also included here.
..             * <SyncLoop> - This contains information about how you want to access values of the motors inside your robot. You can describe loops that obtains certain values at a given frequency.

.. Now lets get a flower and start creating our own simple xml configuration file. An example file has already been provided in the 'resources' folder of your installation of PyPot.

..     #. Create a new file with the extension .xml. 
..     #. Create the Robot opening and closing tags and add a name for you robot like the following::
        
..         <Robot name="Violette">
..         </Robot>
    
..     #. Add some basic EEPROM values that all the motors will use. In the following example we have added two values. The return delay time indicates that motors wait 0 microseconds before replying to messages sent from the controller. The status return level we have chosen ensures that both values of the motors can be read, and status messages are returned when values are written. EEPROM value descriptions can be found #TODO: make EEPROM list and descriptions::
            
..             <EEPROM>
..                 <return_delay_time>0</return_delay_time>
..                 <status_return_level>2</status_return_level>
..             </EEPROM>
            
..     #. Now we should add the controller. On a flower, there is usually only one bus, therefore only one controller is needed. Flowers are made up of RX motors. This means that a USB2Dynamixel device will be used to control it. When you describe your controller, you must include the port that the device is connected to (see :ref:`open_connection`). Add the following code after </EEPROM> tag::
    
..             <DynamixelController type="USB2DXL" port="/dev/ttyACM0">
..             </DynamixelController>
        
..     #. Inside the <DynamixelController> tag you can first list the alarms that you wish to ignore. This is an optional tag, but for the sake of example we have included it here. The following explains that we do not wish to receive messages from the motors if we try to send a position that is outside the allowable limit of the motor. This does not mean that the motor may try to go to this position, it will only go to its limit and then stop without sending us a warning message::
                
..             <AlarmBlackList>
..                 <ANGLE_LIMIT_ERROR />
..             </AlarmBlackList>
        
..         #TODO: make alarm blacklist optional in the code
    
..     #. Now you have to start thinking a little about how you want to start using your robot. In most cases interaction with the robot will be limited to the reading of current positions of the motors and also the moving of these motors by setting their goal position. You can describe this access in a sync loop that includes the frequency of the read or write cycle and also a list of the motor registers and whether you wish to read 'r' or write 'w' values to them. Each time through the loop the robot will update all the registered that need to be read and will write any new values that need to be updated. This means that the frequency describes the maximum amount of time between changing a value and having it written to the motor or the delay between the current of value of the motor and the value that has been read. Below is an example of two such loops::
            
..             <SyncLoop>
..                 <Loop frequency='50'>
..                     <position access='r' />
..                     <goal_position access='w' />
..                 </Loop>
            
..                 <Loop frequency='1'>
..                     <temperature access='r' />
..                 </Loop>
..             </SyncLoop>

    
..     #. Finally we add the motors that belong on this bus. The attributes are not optional and describe how the motors can be used in the software. The name and id are used to access the motor specifically. Orientation describes whether the motor will act in an anti-clockwise fashion (direct) or clockwise (indirect)::
    
..             <!-- stem -->
..             <DynamixelMotor name="base_pan" id="91" type="RX-64" orientation="direct" offset=0.0>
..             </DynamixelMotor>
..             <DynamixelMotor name="base_tilt_lower" id="92" type="RX-64" orientation="indirect" offset=0.0>
..                 <angle_limits>(-90, 90)</angle_limits>
..             </DynamixelMotor>
..             <DynamixelMotor name="base_tilt_upper" id="93" type="RX-64" orientation="indirect" offset=0.0>
..                 <angle_limits>(-90, 90)</angle_limits>
..             </DynamixelMotor>
..             <DynamixelMotor name="head_pan" id="94" type="RX-28" orientation="direct" offset=0.0>
..             </DynamixelMotor>
..             <DynamixelMotor name="head_tilt_lower" id="95" type="RX-28" orientation="indirect" offset=0.0>
..                 <angle_limits>(-90, 90)</angle_limits>
..             </DynamixelMotor>
..             <DynamixelMotor name="head_tilt_upper" id="96" type="RX-28" orientation="indirect" offset=0.0>
..                 <angle_limits>(-90, 90)</angle_limits>
..             </DynamixelMotor>
        
..     #. This is all you need to create and interact with your robot. All that remains is to connect your robot to your computer. To create your robot, you need to send it the location of your xml file in a string so that it can convert all the custom settings you have placed here and create you a robot. Here is an example of how to create your first robot and start using it::
    
..             import pypot.robot
        
..             file = './resources/flower.xml'
..             robot = pypot.robot.Robot.from_configuration(file)
        
..             robot.base_pan.model
..             >>>'RX-64'
        
..             robot.base_pan.current_position
..             >>> 79.4
        
..             robot.base_pan.goal_position = 0
    
.. Now you have a robot that is reading and writing values to each motor in a continual loop. Whenever you access these values, you are accessing the most recent version of this value that has been read within the frequency of the loop. This parallelises the procedure, reducing the need to wait for a read procedure of the motors in order to access data (this can take some time) so that algorithms with heavy computation do not encounter a bottleneck when values from motors must be known. 
    
.. Now you are ready to create your some behaviours for your robot.
    



.. _sync_loop:

Dynamixel controller and Sync Loop
----------------------------------

Controlling your robot
----------------------

.. Primitive
.. =========

.. What do we call "Primitive"?
.. ----------------------------

.. Starting/pausing primitives
.. ---------------------------

.. Combining primitives
.. --------------------

.. Attaching a primitive to the robot
.. ----------------------------------

.. Writing your own primitive
.. --------------------------

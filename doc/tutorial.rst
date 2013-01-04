.. _tutorial:

Tutorial
********

Installation
============

Low-level communication with robotis motors
===========================================

usb2serial Controller
---------------------

Opening/Closing a communication port
------------------------------------

Finding motors
--------------

Low-level control
-----------------

Defining your custom robot
==========================

Finding the angle limit
-----------------------

Creating a configuration file
-----------------------------

Dynamixel controller and SyncLoop
---------------------------------

Controlling your robot
----------------------

Primitive
=========

What do we call "Primitive"?
----------------------------

Starting/pausing primitives
---------------------------

Combining primitives
--------------------

Attaching a primitive to the robot
----------------------------------

Writing your own primitive
--------------------------

.. .. _tutorial:

.. Tutorial
.. ========

.. Installation
.. ------------

.. Installation of PyPot
.. *********************

.. Before you start, you need to make sure that the following packages are already installed on your computer:
..     * Python 2.7
..     * pyserial 2.6 (at least)
..     * numpy 

.. Open a terminal on your operating system and run the following command::

..     python setup.py install


.. Installation of controller device
.. *********************************

.. There are two devices that have been tested with PyPot that could be used:
..     * USB2AX - this device is designed to manage TTL communication only
..     * USB2Dynamixel - this device can manage both TTL and RS485 communication.

.. On Windows and Mac, it will be necessary to download and install a FTDI (VCP) driver to run the USB2Dynamixel, you can find it here: http://www.ftdichip.com/Drivers/VCP.htm. Linux distributions should already come with an appropriate driver. The USB2AX device should not require a driver installation under MAC or Linux, it should already exist. For Windows XP, it should automatically install the correct driver. See :doc:`Known Issues </knownissues>` for more information on these devices.

.. On the side of the USB2Dynamixel there is a switch. This is used to select the bus you wish to communicate on. This means that you cannot control two different bus protocols at the same time.



.. Making Connections
.. ------------------

.. .. _open_connection:

.. Opening a Connection
.. ********************

.. In order to open a connection with the device, you will need to know what port it is connected to. PyPot has a function :func:`~pypot.dynamixel.get_available_ports` which will try to auto-discover any compatible devices connected to the communication ports. 

.. # TODO: write the exact explanation here

.. To create a connection, open up a python terminal and type the following code::

..     import pypot.dynamixel
    
..     port = pypot.dynamixel.get_available_ports()[0]
..     dxl_io = pypot.dynamixel.DynamixelIO(port)
    
.. This should open a connection through a virtual communication port to your device. 
.. In fact, when you open a connection with your device as above, it is important to note that it will open a connection using a default baud rate and timeout; see :class:`pypot.dynamixel.DynamixelIO` for more details. To communicate with the motors, you must ensure that this baud rate is the same baud rate that the motors are configure to use. New motors may not be automatically configured to the default baud rate, please see http://support.robotis.com/en/product/dxl_main.htm to find out what the default baud configuration is.


.. Finding and Connecting Motors
.. *****************************

.. Pypot has been designed to work specifically with the Robotis range of motors. These motors use two different protocols to communicate: TTL (3 wire bus) and RS485 (4 wire Bus). The motors can be daisey chained together with other types of motors on the same bus *as long as the bus communicates using the same protocol*. This means that MX-28 and AX-12 can communicate on the same bus, but cannot be connected to a RX-28.

.. All motors work sufficiently well with a 12V supply. Some motors can use more than 12V but you must be careful not to connect an 18V supply on a bus that contains motors that can only use 12V! Connect this 12V SMPS supply (switch mode power supply) to a Robotis SMPS2Dynamixel device which regulates the voltage coming from the SMPS. Connect your controller device and a single motor to this SMPS2Dynamixel. 

.. Open your python terminal and create your controller as described in the above section :ref:`open_connection`.
    
.. To detect the motor and find its id you can scan the bus. To avoid spending a long time searching all possible values, you can add a list of values to test::

..     dxl_io.scan([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
..     >>> [4]
    
.. Or, you can use the shorthand::

..     dxl_io.scan(range(10))
..     >>> [4]

.. This should produce a list of the ids of the motors that are connected to the bus. Each motor on the bus must have a unique id. This means that unless your motors have been configured in advance, it is better to connect them one by one to ensure they all have unique ids first.

.. Now we have the id of the motor connected, we can begin to access its functions by using this id. Try to find out the present position (in degrees) of the motor by typing the following::

..     dxl_io.get_position(4)
..     >>> 67.8
    
.. You can also write a goal position (in degrees) to the motor using the following::

..     dxl_io.set_position(4, 0) 

.. The motors are handled in degrees where 0 is considered the central point of the motor turn. For the MX motors, the end points are -180° and 180°. For the AX and RX motors, these end points are -150° to 150°. 

.. In Pypot, to handle the low level set-up of the controllers, motors and structure of the robot, we use configuration files.


.. Making Robots!!!!!
.. ------------------

.. Creating a Configuration File
.. *****************************

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
    

.. Making Robot Behaviours
.. -----------------------

.. Making a Robot Primitive
.. ************************



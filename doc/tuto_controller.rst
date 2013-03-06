
Robot Controller
================

Using the robot abstraction
---------------------------

While the :doc:`tuto_low_level` provides access to all functionalities of the dynamixel motors, it forces you to have synchronous calls which can take a non-negligable amount of time. In particular, most programs will need to have a really fast read/write synchronization loop, where we typically read all motor position, speed, load and set new values, while in parallel we would like to have higher level code that computes those new values. This is pretty much what the robot abstraction is doing for you. More precisely, through the use of the class :class:`~pypot.robot.robot.Robot` you can:
    * automatically initialize all connections (make transparent the use of multiple USB2serial connections),
    * automatically define accessor for motors and their most frequently used registers (such as :attr:`~pypot.dynamixel.motor.DxlMotor.goal_position`, :attr:`~pypot.dynamixel.motor.DxlMotor.present_speed`, :attr:`~pypot.dynamixel.motor.DxlMotor.present_load`, :attr:`~pypot.dynamixel.motor.DxlMXMotor.pid`, :attr:`~pypot.dynamixel.motor.DxlMotor.compliant`),
    * define :attr:`~pypot.dynamixel.motor.DxlMotor.offset` and :attr:`~pypot.dynamixel.motor.DxlMotor.direct` attributes for motors,
    * define read/write synchronization loop that will run in background.
    
We will first see how to define your robot thanks to the writing of a :ref:`configuration file <config_file>`, then we will describe how to set up :ref:`synchronization loops <sync_loop>`. Finally, we will show how to easily :ref:`control this robot through aynchronous calls <control_robot>`. 
    


.. _config_file:

Writing a configuration file
----------------------------

The configuration file, written in xml, contains several important features that help build both your robot and the software to manage you robot. The important features are listed below:
    * **<Robot>** - The root of the configuration file.
    * **<DxlController>** - This tag holds the information pertaining to a controller and all the items connected to its bus.
    * **<DxlMotor>** - This is a description of all the custom setup values for each motor. Meta information, such as the motor access name or orientation, is also included here. It is also inside this markup that you will set the angle limits of the motor.
    * **<DxlMotorGroup>** - This is used to define alias of a group of motors (e.g. left_leg).

.. note:: Your configuration file can be located anywhere on your filesystem. It does not need to be in the resources folder.

Now let's start writing your own configuration file. It is probably easier to start from one of the example provided with PyPot and modify it:

    #. Create a new file with the extension .xml.
    #. Create the Robot opening and closing tags and add a name for you robot like the following::
        
        <Robot name="Violette">
        </Robot>
    
    #. Now we should add the controller. You can have a single or multiple :class:`~pypot.dynamixel.controller.DxlController`. For each of them, you should indicate whether or not to use the SYNC_READ instruction (only the USB2AX device currently supported it). When you describe your controller, you must also include the port that the device is connected to (see :ref:`open_connection`)::

            <DxlController port="/dev/ttyACM0" sync_read="False">
            </DxlController>
        
    #. Then we add the motors that belong on this bus. The attributes are not optional and describe how the motors can be used in the software. You have to specify the type of motor, it will change which attributes are available (e.g. compliance margin versus pid gains). The name and id are used to access the motor specifically. Orientation describes whether the motor will act in an anti-clockwise fashion (direct) or clockwise (indirect). You should also provide the angle limits of your motor. They will be checked automatically at every start up and changed if needed::
    
            <DxlMotor name="base_pan" id="31" type="RX-64" orientation="direct" offset="22.5">
                <angle_limits>(-67.5, 112.5)</angle_limits>
            </DxlMotor>
            <DxlMotor name="base_tilt_lower" id="32" type="RX-64" orientation="direct" offset="0.0">
                <angle_limits>(-90, 90)</angle_limits>
            </DxlMotor>
            
    #. Finally, you can define the different motors group corresponding to the structure of your robot. You only need to define your motors inside the DxlMotorGroup markup to include them in a group. A group can also be included inside another group::
    
            <DxlMotorGroup name="arms">
                <DxlMotorGroup name="left_arm">
                    <DxlMotor name="left_shoulder_pan" id="12" type="RX-28" orientation="indirect" offset="-67.5">
                        <angle_limits>(-150, 150)</angle_limits>
                    </DxlMotor>
                    ...
                </DxlMotorGroup>
                ...
            </DxlMotorGroup>
         
        
    #. This is all you need to create and interact with your robot. All that remains is to connect your robot to your computer. To create your robot, you need to send it the location of your xml file in a string so that it can convert all the custom settings you have placed here and create you a robot. Here is an example of how to create your first robot and start using it::
    
            import pypot.robot
            
            robot = pypot.robot.from_configuration(my_config_file)
            robot.start_sync()
            
            for m in robot.left_arm:
                print m.present_position
    

.. _sync_loop:

Dynamixel controller and Synchronization Loop
---------------------------------------------

As indicated above, the :class:`~pypot.robot.robot.Robot` held instances of :class:`~pypot.dynamixel.motor.DxlMotor`. Each of this instance represents a real motor of your physical robot. The attributes of those "software" motors are automatically synchronized with the real "hardware" motors. In order to do that, the :class:`~pypot.robot.robot.Robot` class uses a :class:`~pypot.dynamixel.controller.DxlController` which defines synchronization loops that will read/write the registers of dynamixel motors at a predefined frequency.

.. warning:: The synchronization loops will try to run at the defined frequency, however don't forget that you are limited by the bus bandwidth! For instance, depending on your robot you will not be able to read/write the position of all motors at 100Hz. Moreover, the loops are implemented as python thread and we can thus not guarantee the exact frequency of the loop.

If you looked closely at the example above, you could have noticed that even without defining any controller nor synchronization loop, you can already read the present position of the motors. Indeed, by default the class :class:`~pypot.robot.robot.Robot` uses a particular controller :class:`~pypot.dynamixel.controller.BaseDxlController` which already defines synchronization loops. More precisely, this controller:
        * reads the present position, speed, load at 50Hz,
        * writes the goal position, moving speed and torque limit at 50Hz,
        * writes the pid or compliance margin/slope (depending on the type of motor) at 10Hz,
        * reads the present temperature and voltage at 1Hz.

So, in most case you should not have to worry about synchronization loop and it should directly work. Off course, if you want to synchronize other values than the ones listed above you will have to modify this default beahvior.

.. note:: With the current version of PyPot, you can not indicate in the xml file which subclasses of :class:`~pypot.dynamixel.controller.DxlController` you want to use. This feature should be added in the next version. If you want to use your own controller, you should either modify the xml parser, modify the :class:`~pypot.dynamixel.controller.BaseDxlController` class or directly instatiate the :class:`~pypot.robot.robot.Robot` class.

To start all the synchronization loops, you only need to call the :meth:`~pypot.robot.robot.Robot.start_sync` method. You can also stop the synchronization if needed (see the :meth:`~pypot.robot.robot.Robot.stop_sync` method)::

    import pypot.robot
    
    robot = pypot.robot.from_configuration(my_config_file)
    robot.start_sync()
    
.. note:: You should never set values to motors before starting the synchronization loop.

Now you have a robot that is reading and writing values to each motor in a continual loop. Whenever you access these values, you are accessing the most recent version of this value that has been read within the frequency of the loop. This parallelises the procedure, reducing the need to wait for a read procedure of the motors in order to access data (this can take some time) so that algorithms with heavy computation do not encounter a bottleneck when values from motors must be known. 
    
Now you are ready to create your some behaviors for your robot.


.. _control_robot:

Controlling your robot
----------------------

As shown in the examples above, the robot class let you directly access the different motors. For instance, let's assume we are working with an Ergo-robot you could write::

    import pypot.robot
    
    ergo_robot = pypot.robot.from_configuration('resources/ergo_robot.xml')
    ergo_start_sync()

    # Note that all these calls will return immediatly, 
    # even if the orders are not directly sent.
    for m in ergo_robot.base:
        m.compliant = False
        m.goal_position = 0

    # This will return the last synchronized value
    print ergo_robot.base_pan.present_position
    
For a complete list of all the attributes that you can access, you should refer to the :class:`~pypot.dynamixel.motor.DxlMotor` API.

As an example of what you can easily do with the Robot API, we are going to write a simple program that will make a robot with two motors move with sinusoidal motions. More precisely, we will apply a sinusoid to one motor and the other one will read the value of the first motor and use it as its own goal position. We will still use an Ergo-robot as example::

    import time
    import numpy

    import pypot.robot
    
    amp = 30
    freq = 0.5
    
    ergo_robot = pypot.robot.from_configuration('resources/ergo_robot.xml')
    ergo_robot.start_sync()
    
    # Put the robot in its initial position
    for m in ergo_robot.motors: # Note that we always provide an alias for all motors.
        m.compliant = False
        m.goal_position = 0
        
    # Wait for the robot to actually reach the base position.
    time.sleep(2)
    
    # Do the sinusoidal motions for 10 seconds
    t0 = time.time()

    while True:
        t = time.time() - t0
        
        if t > 10:
            break

        pos = amp * numpy.sin(2 * numpy.pi * freq * t)
        
        ergo_robot.base_pan.goal_position = pos
        
        # In order to make the other sinus more visible,
        # we apply it with an opposite phase and we increase the amplitude.
        ergo_robot.head_pan.goal_position = -1.5 * ergo_robot.base_pan.present_position
        
        # We want to run this loop at 50Hz.       
        time.sleep(0.02)
    

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

.. _tutorial:

Tutorial
********


PyPot handles the communication with dynamixel motors from robotis. Using a USB communication device such as USB2DYNAMIXEL or USB2AX, you can open serial communication with robotis motors (MX, RX, AX) using communication protocols TTL or RS485. More specifically, it allows easy access (both reading and writing) to the different registers of any dynamixel motors. Those registers includes values such as position, speed or torque. The whole list of registers can directly be found on the robotis website http://support.robotis.com/en/product/dxl_main.htm.

You can access the register of the motors through two different ways:

* **Low-level API:** In the first case, you can get or set a value to a motor by directly sending a request and waiting for the motor to answer. Here, you only use the low level API to communicate with the motor (refer to section :ref:`low_level` for more details).

* **Controller API:** In the second case, you define requests which will automatically be sent at a predefined frequency. The values obtained from the requests are stored in a local copy that you can freely access at any time. However, you can only access the last synchronized value. This second method encapsulate the first approach to prevent you from writing repetitive request (refer to section :ref:`controller` for further details).

While the second approach allows the writing of simpler code without detailed knowledge of how the communication with robotis motor works, the first approach may allow for more performance through fine tuning of the communication needed in  particular applications. Examples of both approaches will be provided in the next sections.


.. _low_level:

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

    print 'ports found', ports

    print 'connecting on the first available port:', ports[0]
    dxl_io = pypot.dynamixel.DxlIO(ports[0])

This should open a connection through a virtual communication port to your device.

.. warning:: It is important to note that it will open a connection using a default baud rate. By default your motors are set up to work on the robotis default baud rate (57140) while PyPot is set up to work with a 1000000 baud rate. To communicate with your motors, you must ensure that this baud rate is the same baud rate that the motors are configure to use. So, you will need to change either the configuration of your motors (see :ref:`Herborist <herborist>` section) or change the default baud rate of your connection.

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

.. note:: You also can modify the timeout to speed up the scanning. Be careful though, as this could result in loosing messages.


Low-level control
-----------------

Now we have the id of the motors connected, we can begin to access their functions by using their id. Try to find out the present position (in degrees) of the motor by typing the following::

    dxl_io.get_present_position((4, ))
    >>> (67.8, )

You can also write a goal position (in degrees) to the motor using the following::

    dxl_io.set_goal_position({4: 0})

The motors are handled in degrees where 0 is considered the central point of the motor turn. For the MX motors, the end points are -180° and 180°. For the AX and RX motors, these end points are -150° to 150°.

.. warning:: As you can see on the example above, you should always pass the id parameter as a list. This is intended as getting a value from several motors takes the same time as getting a value from a single motor (thanks to the SYNC_READ instruction). Similarly, we use dictionary with pairs of (id, value) to set value to a specific register of motors and benefit from the SYNC_WRITE instruction.

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



Thanks to PyPot, you can access all registers of your motors using the same syntax (e.g. :meth:`~pypot.dynamixel.io.DxlIO.get_present_speed`, :meth:`~pypot.dynamixel.io.DxlIO.set_max_torque`, :meth:`~pypot.dynamixel.io.DxlIO.get_pid_gain`). Some shortcuts have been provided to make the code more readable (e.g. :meth:`~pypot.dynamixel.io.DxlIO.enable_torque` instead of set_torque_enabled). All the getter functions takes a list of ids as argument and the setter takes a dictionary of (id: value) pairs. You can refer to the documentation of :class:`~pypot.dynamixel.io.DxlIO` for a complete list of all the available methods.


.. note:: PyPot provides an easy way to extend the code and automatically create methods to access new registers added by robotis.


.. _controller:

Robot Controller
================

Using the robot abstraction
---------------------------

While the :ref:`low_level` provides access to all functionalities of the dynamixel motors, it forces you to have synchronous calls which can take a non-negligible amount of time. In particular, most programs will need to have a really fast read/write synchronization loop, where we typically read all motor position, speed, load and set new values, while in parallel we would like to have higher level code that computes those new values. This is pretty much what the robot abstraction is doing for you. More precisely, through the use of the class :class:`~pypot.robot.robot.Robot` you can:

* automatically initialize all connections (make transparent the use of multiple USB2serial connections),
* define :attr:`~pypot.dynamixel.motor.DxlMotor.offset` and :attr:`~pypot.dynamixel.motor.DxlMotor.direct` attributes   for motors,
* automatically define accessor for motors and their most frequently used registers (such as :attr:`~pypot.dynamixel.motor.DxlMotor.goal_position`, :attr:`~pypot.dynamixel.motor.DxlMotor.present_speed`, :attr:`~pypot.dynamixel.motor.DxlMotor.present_load`, :attr:`~pypot.dynamixel.motor.DxlMXMotor.pid`, :attr:`~pypot.dynamixel.motor.DxlMotor.compliant`),
* define read/write synchronization loop that will run in background.


We will first see how to define your robot thanks to the writing of a :ref:`configuration file <config_file>`, then we will describe how to set up :ref:`synchronization loops <sync_loop>`. Finally, we will show how to easily :ref:`control this robot through asynchronous commands <control_robot>`.



.. _config_file:

Writing a configuration file
----------------------------

The configuration file, written in xml, contains several important features that help build both your robot and the software to manage you robot. The important features are listed below:

* **<Robot>** - The root of the configuration file.
* **<DxlController>** - This tag holds the information pertaining to a controller and all the items connected to its bus.
* **<DxlMotor>** - This is a description of all the custom setup values for each motor. Meta information, such as the motor access name or orientation, is also included here. It is also inside this markup that you will set the angle limits of the motor.
* **<DxlMotorGroup>** - This is used to define alias of a group of motors (e.g. left_leg).

Now let's start writing your own configuration file. It is probably easier to start from one of the example provided with PyPot and modify it:

#. Create a new file with the extension .xml. Your configuration file can be located anywhere on your filesystem. It does not need to be in the resources folder.

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

So, in most case you should not have to worry about synchronization loop and it should directly work. Off course, if you want to synchronize other values than the ones listed above you will have to modify this default behavior.

.. note:: With the current version of PyPot, you can not indicate in the xml file which subclasses of :class:`~pypot.dynamixel.controller.DxlController` you want to use. This feature should be added in the next version. If you want to use your own controller, you should either modify the xml parser, modify the :class:`~pypot.dynamixel.controller.BaseDxlController` class or directly instantiate the :class:`~pypot.robot.robot.Robot` class.

To start all the synchronization loops, you only need to call the :meth:`~pypot.robot.robot.Robot.start_sync` method. You can also stop the synchronization if needed (see the :meth:`~pypot.robot.robot.Robot.stop_sync` method)::

    import pypot.robot

    robot = pypot.robot.from_configuration(my_config_file)
    robot.start_sync()

.. warning:: You should never set values to motors before starting the synchronization loop.

Now you have a robot that is reading and writing values to each motor in an infinite loop. Whenever you access these values, you are accessing only their most recent versions that have been read at the frequency of the loop. This automatically make the synchronization loop run in background. You do not need to wait the answer of a read command to access data (this can take some time) so that algorithms with heavy computation do not encounter a bottleneck when values from motors must be known.

Now you are ready to create some behaviors for your robot.


.. _control_robot:

Controlling your robot
----------------------

Controlling in position
+++++++++++++++++++++++

As shown in the examples above, the robot class let you directly access the different motors. For instance, let's assume we are working with an Ergo-robot, you could then write::

    import pypot.robot

    ergo_robot = pypot.robot.from_configuration('resources/ergo_robot.xml')
    ergo_start_sync()

    # Note that all these calls will return immediately,
    # and the orders will not be directly sent
    # (they will be sent during the next write loop iteration).
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


Controlling in speed
++++++++++++++++++++

Thanks to the :attr:`~pypot.dynamixel.motor.DxlMotor.goal_speed` property you can also control your robot in speed. More precisely, by setting :attr:`~pypot.dynamixel.motor.DxlMotor.goal_speed` you will change the :attr:`~pypot.dynamixel.motor.DxlMotor.moving_speed` of your motor but you will also automatically change the :attr:`~pypot.dynamixel.motor.DxlMotor.goal_position` that will be set to the angle limit in the desired direction.


.. note:: You could also use the wheel mode settings where you can directly change the :attr:`~pypot.dynamixel.motor.DxlMotor.moving_speed`. Nevertheless, while the motor will turn infinitely with the wheel mode, here with the :attr:`~pypot.dynamixel.motor.DxlMotor.goal_speed` the motor will still respect the angle limits.


As an example, you could write::

    t = numpy.arange(0, 10, 0.01)
    speeds = amp * numpy.cos(2 * numpy.pi * freq * t)

    positions = []

    for s in speeds:
        ergo_robot.head_pan.goal_speed = s
        positions.append(ergo_robot.head_pan.present_position)
        time.sleep(0.05)

    # By applying a cosinus on the speed
    # You observe a sinusoid on the position
    plot(positions)

.. warning:: If you set both :attr:`~pypot.dynamixel.motor.DxlMotor.goal_speed` and :attr:`~pypot.dynamixel.motor.DxlMotor.goal_position` only the last command will be executed. Unless you know what you are doing, you should avoid to mix these both approaches.

Primitive
=========

In the previous sections, we have shown how to make a simple behavior thanks to the :class:`~pypot.robot.Robot` abstraction. But how to combine those elementary behaviors into something more complex? You could use threads and do it manually, but we provide the :class:`~pypot.primitive.Primitive` to abstract most of the work for you.

What do we call "Primitive"?
----------------------------

We call :class:`~pypot.primitive.primitive.Primitive` any simple or complex behavior applied to a :class:`~pypot.robot.robot.Robot`. A primitive can access all sensors and effectors in the robot. A primitive is supposed to be independent of other primitives. In particular, a primitive is not aware of the other primitives running on the robot at the same time. We imagine those primitives as elementary blocks that can be combined to create more complex blocks in a hierarchical manner.

.. note:: The independence of primitives is really important when you create complex behaviors - such as balance - where many primitives are needed. Adding another primitive - such as walking - should be direct and not force you to rewrite everything. Furthermore, the balance primitive could also be combined with another behavior - such as shoot a ball - without modifying it.

To ensure this independence, the primitive is running in a sort of sandbox. More precisely, this means that the primitive has not direct access to the robot. It can only request commands (e.g. set a new goal position of a motor) to a :class:`~pypot.primitive.manager.PrimitiveManager` which transmits them to the "real" robot. As multiple primitives can run on the robot at the same time, their request orders are combined by the manager.

.. note:: The primitives all share the same manager. In further versions, we would like to move from this linear combination of all primitives to a hierarchical structure and have different layer of managers.

The manager uses a filter function to combine all orders sent by primitives. By default, this filter function is a simple mean but you can choose your own specific filter (e.g. add function).

.. warning:: You should not mix control through primitives and direct control through the :class:`~pypot.robot.robot.Robot`. Indeed, the primitive manager will overwrite your orders at its refresh frequency: i.e. it will look like only the commands send through primitives will be taken into account.

.. _write_own_prim:

Writing your own primitive
--------------------------

To write you own primitive, you have to subclass the :class:`~pypot.primitive.primitive.Primitive` class. It provides you with basic mechanisms (e.g. connection to the manager, setup of the thread) to allow you to directly "plug" your primitive to your robot and run it.

.. note:: You should always call the super constructor if you override the :meth:`~pypot.primitive.primitive.Primitive.__init__` method.

As an example, let's write a simple primitive that recreate the dance behavior written in the :ref:`dance_` section::

    import time

    import pypot.primitive

    class DancePrimitive(pypot.primitive.Primitive):
        def run(self, amp=30, freq=0.5):
            # self.elapsed_time gives you the time (in s) since the primitive has been running
            while self.elapsed_time < 30:
                x = amp * numpy.sin(2 * numpy.pi * freq * self.elapsed_time)

                self.robot.base_pan.goal_position = x
                self.robot.head_pan.goal_position = -x

                time.sleep(0.02)

To run this primitive on your robot, you simply have to do::

    ergo_robot = pypot.robot.from_configuration(...)
    ergo_robot.start_sync()

    dance = DancePrimitive(ergo_robot)
    dance.start()


If you want to make the dance primitive infinite you can use the :class:`~pypot.primitive.primitive.LoopPrimitive` class::

    class LoopDancePrimitive(pypot.primitive.LoopPrimitive):
        # The update function is automatically called at the frequency given on the constructor
        def update(self, amp=30, freq=0.5):
            x = amp * numpy.sin(2 * numpy.pi * freq * self.elapsed_time)

            self.robot.base_pan.goal_position = x
            self.robot.head_pan.goal_position = -x

And then runs it with::

    ergo_robot = pypot.robot.from_configuration(...)
    ergo_robot.start_sync()

    dance = LoopDancePrimitive(ergo_robot, 50)
    # The robot will dance until you call dance.stop()
    dance.start()


.. warning:: When writing your own primitive, you should always keep in mind that you should never directly pass the robot or its motors as argument and access them directly. You have to access them through the self.robot and self.robot.motors properties. Indeed, at instantiation the :class:`~pypot.robot.robot.Robot` (resp. :class:`~pypot.dynamixel.motor.DxlMotor`) instance is transformed into a :class:`~pypot.primitive.primitive.MockupRobot` (resp. :class:`~pypot.primitive.primitive.MockupMotor`). Those class are used to intercept the orders sent and forward them to the :class:`~pypot.primitive.manager.PrimitiveManager` which will combine them. By directly accessing the "real" motor or robot you circumvent this mechanism and break the sandboxing. If you have to specify a list of motors to your primitive (e.g. apply the sinusoid primitive to the specified motors), you should either give the motors name and access the motors within the primitive or transform the list of :class:`~pypot.dynamixel.motor.DxlMotor` into :class:`~pypot.primitive.primitive.MockupMotor` thanks to the :meth:`~pypot.primitive.primitive.Primitive.get_mockup_motor` method.
    For instance::

        class MyDummyPrimitive(pypot.primitive.Primitive):
            def run(self, motors_name):
                motors = [getattr(self.robot, name) for name in motors_name]

                while True:
                    for m in fake_motors:
                        ...

    or::

        class MyDummyPrimitive(pypot.primitive.Primitive):
            def run(self, motors):
                fake_motors = [self.get_mockup_motor(m) for m in motors]

                while True:
                    for m in fake_motors:
                        ...



Starting/pausing primitives
---------------------------

The primitive can be :meth:`~pypot.primitive.primitive.Primitive.start`, :meth:`~pypot.primitive.primitive.Primitive.stop`, :meth:`~pypot.primitive.primitive.Primitive.pause` and :meth:`~pypot.primitive.primitive.Primitive.resume`. Unlike regular python thread, primitive can be restart by calling again the :meth:`~pypot.primitive.primitive.Primitive.start` method.

When overriding the :class:`~pypot.primitive.primitive.Primitive`, you are responsible for correctly handling those events. For instance, the stop method will only trigger the should stop event that you should watch in your run loop and break it when the event is set. In particular, you should check the :meth:`~pypot.primitive.primitive.Primitive.should_stop` and :meth:`~pypot.primitive.primitive.Primitive.should_pause` in your run loop. You can also use the :meth:`~pypot.primitive.primitive.Primitive.wait_to_stop` and :meth:`~pypot.primitive.primitive.Primitive.wait_to_resume` to wait until the commands have really been executed.

.. note:: You can refer to the source code of the :class:`~pypot.primitive.primitive.LoopPrimitive` for an example of how to correctly handle all these events.


Attaching a primitive to the robot
----------------------------------

In the previous section, we explain that the primitives run in a sandbox in the sense that they are not aware of the other primitives running at the same time. In fact, this is not exactly true. More precisely, a primitive can access everything attached to the robot: e.g. motors, sensors. But you can also attach a primitive to the robot.

Let's go back on our DancePrimitive example. You can write::

    ergo_robot = pypot.robot.from_configuration(...)
    ergo_robot.start_sync()

    ergo_robot.attach_primitive(DancePrimitive(ergo_robot), 'dance')
    ergo_robot.dance.start()

By attaching a primitive to the robot, you make it accessible from within other primitive.

For instance you could then write::

    class SelectorPrimitive(pypot.primitive.Primitive):
        def run(self):
            if song == 'my_favorite_song_to_dance' and not self.robot.dance.is_alive():
                self.robot.dance.start()

.. note:: In this case, instantiating the DancePrimitive within the SelectorPrimitive would be another solution.


Remote Access
=============

We add the possibility to remotely access and control your robot through TCP network. This can be useful both to work with client/server architecture (e.g. to separate the low-level control running on an embedded computer and higher-level computation on a more powerful computer) and to allow you to plug your existing code written in another language to the PyPot's API.

We defined a protocol which permits the access of all the robot variables and method (including motors and primitives) via a JSON request. The protocol is entirely described in the section :ref:`remote_protocol` below. Two transport methods have been developed so far:

* HTTP via GET and POST request (see the :ref:`http_server` section)
* ZMQ socket (see the :ref:`zmq_server` section)

The :class:`~pypot.server.request.BaseRequestHandler` has been separated from the server, so you can easily add new transport methods if needed.

.. warning:: For the moment, the server is defined as a primitive, so multiple requests will not be automatically combined but instead the last request will win. In further version, it will be possible to spawn each client in a separate primitive.

As an example of what you can do, here is the code of getting the load of a motor and changing its position::

    import zmq

    robot = pypot.robot.from_configuration(...)
    robot.start_sync()

    server = pypot.server.ZMQServer(robot, host, port)
    server.start()

    c = zmq.Context()
    s = c.socket(zmq.REQ)

    req = {
        'get': {motor_name: ('present_load', )},
        'set': {motor_name: {'goal_position': 20.0}}
    }

    s.send_json(req)
    answer = s.recv_json()

.. _remote_protocol:

Protocol
--------

Our protocol allows you define three types of requests:

* :ref:`get_req` (to retrieve a motor register value, access a primitive variable)
* :ref:`set_req` (to set a motor register value, modify any variable within the robot instance)
* :ref:`call_req` (to call a method of any object defined within the robot instance, e.g. a primitive)

An entire request is defined as follows::

    req = {
        'get': get_request,
        'set': set_request,
        'call': call_request
    }

.. note:: The field are optional, so you can define a request with only a get field for instance.


.. _get_req:

Get Request
+++++++++++

The get request is constructed as follows::

    get_request = {
        obj_name_1: (var_path_1, var_path_2, ...),
        obj_name_2: (var_path_1, var_path_2, ...),
        ...
    }

.. note:: The var_path can be a complete path such as skeleton.hip.position.x.

For instance, if you write the following get request::

    get_request = {
        'base_tilt_lower': ('present_position', 'present_load'),
        'base_tilt_upper': ('present_temperature', ),
        'dance', ('current_song.filename', ) # Where dance is an attached primitive
    }

It will retrieve the variables robot.base_tilt_lower.present_position, robot.base_tilt_lower.present_load, robot.base_tilt_upper.present_temperature, and robot.dance.current_song.

The server will return something like::

    answer = {
        'get': {
            'base_tilt_lower': {'present_position': 10.0, 'present_load': 23.0},
            'base_tilt_upper': {'present_temperature': 40},
            'dance': {'current_song.filename': 'never_gonna_give_you_up.mp3'}
        }
    }


.. _set_req:

Set Request
+++++++++++

The set request is really similar to the get request. Instead of giving a list of the var_path you want to access, you provide dictionary of (var_path: desired_value)::

    set_request = {
        obj_name_1: {var_path_1: value1, var_path_2: value2, ...},
        obj_name_2: {var_path_1: value1, var_path_2: value2, ...},
        ...
    }

The server will return an empty set field used as an acknowledgment::

    answer = {
        'set': None,
    }

.. _call_req:

Call Request
++++++++++++

You can also build call request as follows::

    call_request = {
        obj_name_1: {meth_name_1: args, meth_name_2: args, ...},
        obj_name_2: {meth_name_1: args, meth_name_2: args, ...},
        ...
    }

.. note:: The argument as passed as a list.


For instance, this request will start the dance primitive::

    call_request = {
        'dance', {'start': ()} # The start method does not take any argument so we pass the empty list.
    }

The server will return the result of the called methods::

    answer = {
        'call': {
            'dance': {'start': None}, # The start methods does not return anything.
        }
    }

.. _zmq_server:

Zmq Server
----------

The Zmq Server used a Zmq socket to send (resp. receive) JSON request (JSON answer). It is based on the REQ/REP pattern. So you should always alternate sending and receiving. It will probably be switched to PUB/SUB soon.

Zmq has been chosen as it has been binded to most language (http://zeromq.org/bindings:_start) and can thus be used to connect code from other language to PyPot. For instance, we used it to connect RLPark (a Java reinforcement learning library) to PyPot.

Here is an example of how you can create a zmq server and send request::

    import zmq

    robot = pypot.robot.from_configuration(...)
    robot.start_sync()

    server = pypot.server.ZMQServer(robot, host, port)
    server.start()

    c = zmq.Context()
    s = c.socket(zmq.REQ)
    s.connect('tcp://{}:{}'.format(host, port))

    req = {
        'get': {motor_name: ('present_load', )},
        'set': {motor_name: {'goal_position': 20.0}}
    }

    s.send_json(req)
    answer = s.recv_json()

.. note:: The zmq server is faster than the HTTP version and should be preferred when working with high frequency control loops.

.. _http_server:

Http Server
-----------

The HTTPServer is based on the bottle python framework (http://bottlepy.org/). We have developed a sort of REST API based on the protocol described above:

* GET /motor/list.json
* GET /primitive/list.json
* GET /motor/<name>/register.json (or GET /<name>/register.json)
* GET /motor/<name>/<register> (or GET /<name>/<register>)
* POST /motor/<name>/<register> (or POST /<name>/<register>)
* POST /primitive/<prim_name>/call/<meth_name> (or GET /<prim_name>/call/<meth_name>)
* POST /request.json

An example of how you can use the HTTP server::

    import urllib2
    import json
    import time

    import pypot.robot
    import pypot.server

    robot = pypot.robot.from_configuration(...)
    robot.start_sync()

    server = pypot.server.HTTPServer(robot, host, port)
    server.start()

    time.sleep(1) # Make sure the server is really started

    url = 'http://{}:{}/motor/list.json'.format(host, port)
    print urllib2.urlopen(url).read()

    url = 'http://{}:{}/motor/base_tilt_lower/goal_position'.format(host, port)
    data = 20.0
    r = urllib2.Request(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    print urllib2.urlopen(r).read()

.. note:: Note that the http server will always return a dictionary (see http://haacked.com/archive/2009/06/24/json-hijacking.aspx for an explanation).

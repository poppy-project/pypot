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


We will first see how to define your robot thanks to the writing of a :ref:`configuration <config_file>`, then we will describe how to set up :ref:`synchronization loops <sync_loop>`. Finally, we will show how to easily :ref:`control this robot through asynchronous commands <control_robot>`.



.. _config_file:

Writing the configuration
-------------------------

The configuration, described as a Python dictionary, contains several important features that help build both your robot and the software to manage you robot. The important fields are listed below:

* **controllers** - This key holds the information pertaining to a controller and all the items connected to its bus.
* **motors** - This is a description of all the custom setup values for each motor. Meta information, such as the motor access name or orientation, is also included here. It is also there that you will set the angle limits of the motor.
* **motorgroups** - This is used to define alias of a group of motors (e.g. left_leg).

.. note:: The configuration can be written programmatically or can be loaded from any file that can be loaded as a dict (e.g. a JSON file).

Now let's detail each section. To better understand how the configuration is structure it is probably easier to start from one of the example provided with pypot and modify it (e.g. :obj:`pypot.robot.config.ergo_robot_config`):

#. **controllers**: You can have a single or multiple :class:`~pypot.dynamixel.controller.DxlController`. For each of them, you should indicate whether or not to use the SYNC_READ instruction (only the USB2AX device currently supported it). When you describe your controller, you must also include the port that the device is connected to (see :ref:`open_connection`). In this section, you can also specify which robotis protocol to use (if not specified it uses the v1). You also have to specify which motors are attached to this bus. You can either give individual motors or groups (see the sections below)::

        my_config['controllers'] = {}
        my_config['controllers']['upper_body_controler'] = {
            'port': '/dev/ttyUSB0',
            'sync_read': False,
            'attached_motors': ['torso', 'head', 'arms'],
            'protocol': 1,
        }

#. **motorgroups**: Here, you can define the different motors group corresponding to the structure of your robot. It will automatically create an alias for the group. Groups can be nested, i.e. a group can be included inside another group, as in the example below::

        my_config['motorgroups'] = {
            'torso': ['arms', 'head_x', 'head_y'],
            'arms': ['left_arm', 'right_arm'],
            'left_arm': ['l_shoulder_x', 'l_shoulder_y', 'l_elbow'],
            'right_arm': ['r_shoulder_x', 'r_shoulder_y', 'r_elbow']
        }

#. **motors**: Then, you add all the motors. The attributes are not optional and describe how the motors can be used in the software. You have to specify the type of motor, it will change which attributes are available (e.g. compliance margin versus pid gains). The name and id are used to access the motor specifically. Orientation describes whether the motor will act in an anti-clockwise fashion (direct) or clockwise (indirect). You should also provide the angle limits of your motor. They will be checked automatically at every start up and changed if needed::

        my_config['motors'] = {}
        my_config['motors']['l_hip_y'] = {
            'id': 11,
            'type': 'MX-28',
            'orientation': 'direct',
            'offset': 0.0,
            'angle_limit': (-90.0, 90.0),
        }


#. This is all you need to create and interact with your robot. All that remains is to connect your robot to your computer. To create your robot use the :func:`~pypot.robot.config.from_config` function which takes your configuration as an argument. Here is an example of how to create your first robot and start using it::

        import pypot.robot

        robot = pypot.robot.from_config(my_config)

        for m in robot.left_arm:
            print(m.present_position)

#. (optional) If you prefer working with file, you can read/write your config to any format that can be transformed into a dictionary. For instance, you can easily use the JSON format::

    import json

    import pypot.robot

    from pypot.robot.config import ergo_robot_config

    with open('ergo.json', 'w') as f:
        json.dump(ergo_robot_config, f, indent=2)

    ergo = pypot.robot.from_json('ergo.json')


To give you a complete overview of what your config should look like, here is the listing of the Ergo-Robot config dictionary::

    ergo_robot_config = {
        'controllers': {
            'my_dxl_controller': {
                'sync_read': False,
                'attached_motors': ['base', 'tip'],
                'port': 'auto'
            }
        },
        'motorgroups': {
            'base': ['m1', 'm2', 'm3'],
            'tip': ['m4', 'm5', 'm6']
        },
        'motors': {
            'm5': {
                'orientation': 'indirect',
                'type': 'MX-28',
                'id': 15,
                'angle_limit': [-90.0, 90.0],
                'offset': 0.0
            },
            'm4': {
                'orientation': 'direct',
                'type': 'MX-28',
                'id': 14,
                'angle_limit': [-90.0, 90.0],
                'offset': 0.0
            },
            'm6': {
                'orientation': 'indirect',
                'type': 'MX-28',
                'id': 16,
                'angle_limit': [-90.0, 90.0],
                'offset': 0.0
            },
            'm1': {
                'orientation': 'direct',
                'type': 'MX-28', 'id': 11,
                'angle_limit': [-90.0, 90.0],
                'offset': 0.0
            },
            'm3': {
                'orientation': 'indirect',
                'type': 'MX-28',
                'id': 13,
                'angle_limit': [-90.0, 90.0],
                'offset': 0.0
            },
            'm2': {
                'orientation': 'indirect',
                'type': 'MX-28',
                'id': 12,
                'angle_limit': [-90.0, 90.0],
                'offset': 0.0
            }
        }
    }


Since pypot 1.7, you can now set the port to 'auto' in the dictionary. When loading the configuration, pypot will automatically try to find the port with the corresponding attached motor ids.

.. note:: While this is convenient as the same config file can be use on multiple machine, it also slows the creation of the :class:`~pypot.robot.robot.Robot`.


Auto-detection and generation of the configuration
--------------------------------------------------

Pypot provides another way of creating your :class:`~pypot.robot.robot.Robot`. The :func:`~pypot.dynamixel.autodetect_robot` can scan all dynamixel ports plugged and find all connected motors. It then returns the corresponding :class:`~pypot.robot.robot.Robot`. For instance::

    from pypot.dynamixel import autodetect_robot

    my_robot = autodetect_robot()

    for m in my_robot.motors:
        m.goal_position = 0.0

.. note:: As the :func:`~pypot.dynamixel.autodetect_robot` function scans all available ports, it can be quite slow (few seconds). So this should be used to first discover the robot configuration and then export it (see below).

If you have manually created your :class:`~pypot.robot.robot.Robot` (or thanks to the :func:`~pypot.dynamixel.autodetect_robot` function), you can then use the :meth:`~pypot.robot.Robot.to_config` method to export the :class:`~pypot.robot.robot.Robot` current configuration.

This configuration can then be easily saved::

    import json

    config = my_robot.to_config()

    with open('my_robot.json', 'wb') as f:
        json.dump(config, f)

You can then easily re-create your robot::

    from pypot.robot import from_json

    my_robot = from_json('my_robot.json')

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

.. note:: With the current version of pypot, you can not indicate in the configuration which subclasses of :class:`~pypot.dynamixel.controller.DxlController` you want to use. This feature should be added in a future version. If you want to use your own controller, you should either modify the config parser, modify the :class:`~pypot.dynamixel.controller.BaseDxlController` class or directly instantiate the :class:`~pypot.robot.robot.Robot` class.

The synchronization loops are automatically started when instantiating your robot, the method :meth:`~pypot.robot.robot.Robot.start_sync` is directly called. You can also stop the synchronization if needed (see the :meth:`~pypot.robot.robot.Robot.stop_sync` method). Note that prior to version 2, the synchronization is not started by default.

.. warning:: You should never set values to motors when the synchronization is not running.

Now you have a robot that is reading and writing values to each motor in an infinite loop. Whenever you access these values, you are accessing only their most recent versions that have been read at the frequency of the loop. This automatically make the synchronization loop run in background. You do not need to wait the answer of a read command to access data (this can take some time) so that algorithms with heavy computation do not encounter a bottleneck when values from motors must be known.

Now you are ready to create some behaviors for your robot.


.. _control_robot:

Controlling your robot
----------------------

Controlling in position
+++++++++++++++++++++++

As shown in the examples above, the robot class let you directly access the different motors. For instance, let's assume we are working with an Ergo-robot, you could then write::

    import pypot.robot

    from pypot.robot.config import ergo_robot_config

    robot = pypot.robot.from_config(ergo_robot_config)

    # Note that all these calls will return immediately,
    # and the orders will not be directly sent
    # (they will be sent during the next write loop iteration).
    for m in ergo_robot.base:
        m.compliant = False
        m.goal_position = 0

    # This will return the last synchronized value
    print(ergo_robot.base_pan.present_position)

For a complete list of all the attributes that you can access, you should refer to the :class:`~pypot.dynamixel.motor.DxlMotor` API.

As an example of what you can easily do with the Robot API, we are going to write a simple program that will make a robot with two motors move with sinusoidal motions. More precisely, we will apply a sinusoid to one motor and the other one will read the value of the first motor and use it as its own goal position. We will still use an Ergo-robot as example::

    import time
    import numpy

    import pypot.robot

    from pypot.robot.config import ergo_robot_config

    amp = 30
    freq = 0.5

    robot = pypot.robot.from_config(ergo_robot_config)

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

Closing the robot
-----------------

To make sure that everything gets cleaned correctly after you are done using your :class:`~pypot.robot.robot.Robot`, you should always call the :meth:`~pypot.robot.robot.Robot.close` method. Doing so will ensure that all the controllers attached to this robot, and their associated dynamixel serial connection, are correctly stopped and cleaned.

.. note:: Note calling the :meth:`~pypot.robot.robot.Robot.close` method on a :class:`~pypot.robot.robot.Robot` can prevent you from opening it again without terminating your current Python session. Indeed, as the destruction of object is handled by the garbage collector, there is no mechanism which guarantee that we can automatically clean it when destroyed.

When closing the robot, we also send a stop signal to all the primitives running and wait for them to terminate. See section :ref:`my_prim` for details on what we call primitives.

.. warning:: You should be careful that all your primitives correctly respond to the stop signal. Indeed, having a blocking primitive will prevent the :meth:`~pypot.robot.robot.Robot.close` method to terminate (please refer to :ref:`start_prim` for details).

Thanks to the :func:`contextlib.closing` decorator you can easily make sure that the close function of your robot is always called whatever happened inside your code::

  from contextlib import closing

  import pypot.robot

  # The closing decorator make sure that the close function will be called
  # on the object passed as argument when the with block is exited.

  with closing(pypot.robot.from_json('myconfig.json')) as my_robot:
      # do stuff without having to make sure not to forget to close my_robot!
      pass

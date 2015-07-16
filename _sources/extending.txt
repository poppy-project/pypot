.. _extending:

Extending pypot
===============

While pypot has been originally designed for controlling dynamixel based robots, it became rapidly obvious that it would be really useful to easily:

* control other types of motor (e.g. servo-motors controlled using PWM)
* control an entire robot composed of different types of motors (using dynamixel for the legs and smaller servo for the hands for instance)

While it was already possible to do such things in pypot, the library has been partially re-architectured in version 2.x to better reflect those possibilities and most importantly make it easier for contributors to add the layer needed for adding support for other types of motors.

.. note:: While in most of this documentation, we will show how support for other motors can be added, similar methods can be applied to also support other sensors.

The rest of this section will describe the main concept behing pypot's architecture and then give examples of how to extend it.

Pypot's architecture
--------------------

Pypot's architecture is built upon the following basic concepts:

* **I/O**: low-level layer handling the communication with motors or sensors. This abstract layer has been designed to be as generic as possible. The idea is to keep each specific communication protocol separated from the rest of the architecture and allow for an easy replacement of an IO by another one - such an example is detailed in the next section when `dynamixel IO <http://poppy-project.github.io/pypot/pypot.dynamixel.html#module-pypot.dynamixel.io>`_ is replaced by the `communication layout with the VREP <http://poppy-project.github.io/pypot/pypot.vrep.html#module-pypot.vrep.io>`_ simulator.

* **Controller**: set of update loops to keep an (or multiple) "hardware" device(s) up to date with their "software" equivalent. This synchronization can goes only from the hard to the soft (e.g. in the case of a sensor) or both ways (e.g. for reading motor values and sending motor commands). The calls can be asynchronous or synchronous, each controller can have its own refresh frequency. An example of :class:`~pypot.robot.controller.Controller` is the :class:`~pypot.dynamixel.controller.DxlController` which synchronizes position/speed/load of all motors on a dynamixel bus in both directions.

* **Robot**: The robot layer is a pure abstraction which aims at bringing together different types of motors and sensors. This high-level is most likely to be the one accessed by the end-user which wants to directly control the motors of its robot no matter what is the IO used underneath. The robot can be directly created using a `configuration file <http://poppy-project.github.io/pypot/controller.html#writing-the-configuration>`_ describing all IO and Controllers used.

* **Primitive**: independent behaviors applied to a robot. They are not directly accessing the robot registers but are first combined through a `Primitive Manager <http://poppy-project.github.io/pypot/primitive.html>`_ which sends the results of this combination to the robot. This abstraction is used to designed behavioral-unit that can be combined into more complex behaviors (e.g. a walking primitive and and balance primitive combined to obtain a balanced-walking). Primitives are also a convenient way to monitor or remotely access a robot - ensuring some sort of sandboxing.

Those main aspects of pypot's architecture are summarized in the figure below.

.. image:: pypot-archi.jpg
    :width: 60%
    :align: center

Adding another layer
--------------------

If you want to add support for the brand new servo-motors in pypot or the new mindblowing sensor, you are in the right section. As an example of how you should proceed, we will describe how support for the `V-REP simulator <http://www.coppeliarobotics.com>`_ was added and how it allows for a seamless switch from real to simulated robot.

Adding support for the V-REP simulator in pypot could be sum up in three main steps:

* Writing the low-level IO for V-REP.
* Writing the controller to synchronize pypot's :class:`~pypot.robot.robot.Robot` with the V-REP's one.
* Integrates it to a :class:`~pypot.robot.robot.Robot`

Writing a new IO
++++++++++++++++

In pypot's architecture, the IO aims at providing convenient methods to access (read/write) value from a device - which could be a motor, a camera, or a simulator. It is the role of the IO to handle the communication:

* open/close the communication channel,
* encapsulate the protocol.

For example, the :class:`~pypot.dynamixel.io.DxlIO` (for dynamixel buses) open/closes the serial port and provides high-level methods for sending dynamixel packet - e.g. for getting a motor position. Similarly, writing the :class:`~pypot.vrep.io.VrepIO` consists in opening the communication socket to the V-REP simulator (thanks to `V-REP's remote API <http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm>`_) and then encapsulating all methods for getting/setting all the simulated motors registers.

.. warning:: While this is not by any mean mandatory, it is often a good practice to write all IO access as synchronous calls. The higher-level synchronization loop is usually written as a :class:`~pypot.robot.controller.AbstractController`.

The IO should also handle the low-level communication errors. For instance, the :class:`~pypot.dynamixel.io.DxlIO` automatically handles the timeout error to prevent the whole communication to stop.

.. note:: Once the new IO is written most of the integration into pypot should be done! To facilitate the integration of the new IO with the higher layer, we strongly recommend to take inspiration from the existing IO - especially the :class:`~pypot.dynamixel.io.DxlIO` and the :class:`~pypot.vrep.io.VrepIO` ones.

Writing a new Controller
++++++++++++++++++++++++

A :class:`~pypot.robot.controller.Controller` is basically a synchronization loop which role is to keep up to date the state of the device and its "software" equivalent - through the associated IO.

In the case of the :class:`~pypot.dynamixel.controller.DxlController`, it runs a 50Hz loop which reads the actual position/speed/load of the real motor and sets it to the associated register in the :class:`~pypot.dynamixel.motor.DxlMotor`. It also reads the goal position/speed/load set in the :class:`~pypot.dynamixel.motor.DxlMotor` and sends them to the "real" motor.

As most controller will have the same general structure - i.e. calling a sync. method at a predefined frequency - pypot provides an abstract class, the :class:`~pypot.robot.controller.AbstractController`, which does exactly that. If your controller fits within this conception, you should only have to overide the :meth:`~pypot.robot.controller.AbstractController.update` method.

In the case of the :class:`~pypot.vrep.controller.VrepController`, the update loop simply retrieves each motor's present position and send the new target position. A similar approach is used to retrieve values form V-REP sensors.

.. note:: Each controller can run at its own pre-defined frequency and live within its own thread. Thus, the update never blocks the main thread and you can used tight synchronization loop where they are needed (e.g. for motor's command) and slower one when latency is not a big issue (e.g. a temperature sensor).

Integrates it into the Robot
++++++++++++++++++++++++++++

Once you have defined your Controller, you most likely want to define a convenient factory functions (such as :func:`~pypot.robot.config.from_config` or :func:`~pypot.vrep.from_vrep`) allowing users to easily instantiate their :class:`~pypot.robot.robot.Robot` with the new Controller.

By doing so you will permit them to seamlessly uses your interface with this new device without changing the high-level API. For instance, as both the :class:`~pypot.dynamixel.controller.DxlController` and the :class:`~pypot.vrep.controller.VrepController` only interact with the :class:`~pypot.robot.robot.Robot` through getting and setting values into :class:`~pypot.robot.motor.Motor` instances, they can be directly switch.

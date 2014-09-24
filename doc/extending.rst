.. _extending:

Extending pypot
===============

While pypot has been originally designed for controlling dynamixel based robots, it became rapidly obvious that it would be really useful to easily:

* control other types of motor (e.g. servo-motors controlled using PWM)
* control an entire robot composed of different types of motors (using dynamixel for the legs and smaller servo for the hands for instance)

While it was possible to do such thing in pypot, the library has been partially re-architectured in version 2.x to better reflect those possibilities and most importantly make it easier for contributors to add the layer needed for adding support for other types of motors.

.. note:: While in most of this documentation, we will show how support for other motors can be added, similar methods can be applied to support other sensors.

The rest of this section will describe the main concept behing pypot's architecture and then give example of how to extend it.

Pypot's architecture
--------------------

Pypot's architecture is built upon the following basic concepts:

* **I/O**: low-level layer handling the communication with motors or sensors. This abstract layer has been designed to be as generic as possible. The idea is to keep each specific communication protocol separated from the rest of the architecture and allow for an easy replacement of an IO by another - such an example is detailed in the next section when `dynamixel IO <http://poppy-project.github.io/pypot/pypot.dynamixel.html#module-pypot.dynamixel.io>`_ is replaced by the `communication layout with the VREP <http://poppy-project.github.io/pypot/pypot.vrep.html#module-pypot.vrep.io>`_ simulator.

* **Controller**: set of update loops to keep an (or multiple) "hardware" device(s) up to date with their "software" equivalent. This synchronization can goes only from the hard to the soft (e.g. in the case of a sensor) or both ways (e.g. for reading motor values and sending motor commands). The calls can be asynchronous or synchronous, each controller can have its own refresh frequency. An example of :class:`~pypot.robot.controller.Controller` is the :class:`~pypot.dynamixel.controller.DxlController` which synchronizes position/speed/load of all motors on a dynamixel bus in both directions.

* **Robot**: The robot layer is a pure abstraction which aims at bringing together different types of motors and sensors. This high-level is most likely to be the one accessed by the end-user which wants to directly control motors of its robot no matter what is the IO used underneath. The robot can be directly created using a `configuration file <http://poppy-project.github.io/pypot/controller.html#writing-the-configuration>`_ describing all IO and Controllers used.

* **Primitive**: independent behaviors applied to a robot. They are not directly accessing their robot registers but are first combined through a `Primitive Manager <http://poppy-project.github.io/pypot/primitive.html>`_ which sends the results of this combination to the robot. This abstraction is used to designed behavioral-unit that can be combined into more complex behaviors (e.g. a walking and and balance primitive combined to obtain a balanced-walking). Primitives are also convenient way to monitor or remotely access a robot - ensuring some sort of sandboxing.

Those main aspects of pypot's architecture are summarized in the figure below.

.. image:: pypot-archi.pdf
    :width: 60%
    :align: center

Adding another layer
--------------------

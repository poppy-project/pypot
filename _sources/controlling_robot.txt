
Controlling robot
*****************

Pypot handles the communication with dynamixel motors from robotis. Using a USB communication device such as USB2DYNAMIXEL or USB2AX, you can open serial communication with robotis motors (MX, RX, AX and XL320) using communication protocols TTL or RS485. More specifically, it allows easy access (both reading and writing) to the different registers of any dynamixel motors. Those registers includes values such as position, speed or torque. The whole list of registers can directly be found on the `robotis website <http://support.robotis.com/en/product/dxl_main.htm>`_.

You can access the register of the motors through two different ways:

* **Low-level API:** In the first case, you can get or set a value to a motor by directly sending a request and waiting for the motor to answer. Here, you only use the low level API to communicate with the motor (refer to section :ref:`low_level` for more details).

* **Controller API:** In the second case, you define requests which will automatically be sent at a predefined frequency. The values obtained from the requests are stored in a local copy that you can freely access at any time. However, you can only access the last synchronized value. This second method encapsulates the first approach to prevent you from writing repetitive request (refer to section :ref:`controller` for further details).

While the second approach allows the writing of simpler code without detailed knowledge of how the communication with robotis motor works, the first approach may allow for more performance through fine tuning of the communication needed in  particular applications. Examples of both approaches will be provided in the next sections.

.. toctree::
    dynamixel.rst
    controller.rst

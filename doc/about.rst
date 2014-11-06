What is pypot?
==============

.. image:: banderole-pypot.png
    :width: 100%
    :align: center


Pypot is a framework developed in the `Inria FLOWERS <https://flowers.inria.fr/>`_ team to make it easy and fast to control custom robots based on dynamixel motors. This framework provides different level of abstraction corresponding to different types of use. More precisely, you can use pypot to:

* directly control robotis motors through a USB2serial device,
* define the structure of your particular robot and control it through high-level commands.

.. * define primitives and easily combine them to create complex behavior.

Pypot has been entirely written in Python to allow for fast development, easy deployment and quick scripting by non-necessary expert developers. The serial communication is handled through the standard library and thus allows for rather high performance (10ms sensorimotor loop). It is crossed-platform and has been tested on Linux, Windows and Mac OS. It is distributed under the `GPL V3 open source license <http://www.gnu.org/copyleft/gpl.html>`_.

Pypot is also compatible with the `V-REP simulator <http://www.coppeliarobotics.com>`_. This allows you to seamlessly switch from a real robot to its simulated equivalent without having to modify your code.

The next sections describe how to :ref:`install <installation>` pypot on your system and then the :ref:`first steps to control an Ergo-Robot <quickstart>`. If you decide to use pypot and want more details on what you can do with this framework, you can refer to the :ref:`tutorial <tutorial>`.

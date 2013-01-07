Introduction
************

What is PyPot?
==============

PyPot is a framework developed in the `INRIA FLOWERS <https://flowers.inria.fr/>`_ team to make it easy and fast to control custom robots based on dynamixel motors. It has then been extended to make it possible to add custom sensors such as the one based on Arduino. This framework provides different level of abstraction corresponding to different types of use. More precisely, you can use PyPot to:

* directly control robotis motors through a usb2serial device,
* define the structure of your particular robot and control it through high-level command,
* define primitives and easily combine them to create complex behaviors.

PyPot has been entirely written in Python to allow for fast development, easy deployment and quick scripting by non-necessary expert developers. It is based on the standard library to handle the serial communication and thus achieve rather high performance. While it should be crossed-platform, it is currently only supported on Linux and Mac OS.

The next sections describe how to :ref:`install <installation>` PyPot on your system and then the :ref:`first steps to control an Ergo-Robot <quickstart>`. If you decide to use PyPot and want more details on what you can do with this framework you can refer to the :ref:`tutorial <tutorial>`.


.. _installation:

Installation
============

PyPot is a package entirely written in Python. The install process should thus be rather straightforward. PyPot has not been packaged yet and should be built from source. They can be downloaded on bitbucket `here <https://bitbucket.org/pierrerouanet/pypot>`_.

Before you start building PyPot, you need to make sure that the following packages are already installed on your computer:

* `python <http://www.python.org>`_ 2.7
* `pyserial <http://pyserial.sourceforge.net/>`_ 2.6 (or later)
* `numpy <http://www.numpy.org>`_ 

Once it is done, you can build and install PyPot with the classical::

    cd PyPot
    python setup.py build
    python setup.py install


.. _quickstart:

QuickStart: playing with an Ergo-Robot
======================================

Building your own Ergo-Robot
----------------------------

`Ergo-Robots <https://flowers.inria.fr/ergo-robots-fr.php>`_ have been developed for an art exhibition in Fondation Cartier. They are small creatures made from robotis motors and shaped as a stem with a head. They were developed to explore research topics such as artificial curiosity and language games.

.. image:: ErgoRobots.jpg
    :height: 400
    :align: center

You can follow the instructions here to build your own Ergo-Robot before starting playing with it.

Connecting the robot to your computer
-------------------------------------

Now that you have your robot, let's start writing the code necessary to control it.

First, create a work folder wherever you want on your filesystem::

    mkdir my_first_pypot_example

Then, the first step is to create the configuration file for your robot. This file will describe the motor configuration of your robot and make the initialization really easy. Writing this configuration file can be repetitive. Luckily, the PyPot package comes with some examples of configuration file and in particular with a "template" of a configuration file for an Ergo-Robot. Copy this file to your work folder, so you can modify it::

    cd my_first_pypot_example
    cp $(PYPOT_SRC)/resources/ergo_robot.xml .

Open the configuration file with your favorite editor. You only have to modify the usb2serial port and the id of the motors so they correspond to your robot (replace the \*\*\* in the file by the correct values). If you do not know how to get this information, you can refer to the documentation on the :ref:`Herborist tool <herborist>`. Alternatively, you can directly use PyPot::

    import pypot.dynamixel
    
    print pypot.dynamixel.get_available_ports()
    ['/dev/tty.usbserial-A4008aCD', '/dev/tty.usbmodemfd1311']
    
    dxl_io = pypot.dynamixel.DxlIO('/dev/tty.usbserial-A4008aCD')
    print dxl_io.scan()
    [11, 12, 13, 14, 15, 16]
    
Once you have edited the configuration file, you should be able to instantiate your robot directly with PyPot::

    import pypot.robot
    
    ergo_robot = pypot.robot.from_configuration(path_to_my_configuration_file)
    
At this point, if you have not seen any errors it means that you successfully instantiate your first robot!

Controlling your Ergo-Robot
---------------------------

Now let's write a very simple program to make the Ergo-Robot dances a bit. Create a new python file in your work folder and edit it. 

First, add the following lines (we assume that your python script and the configuration file are in the same folder)::

    import pypot.robot
    
    ergo_robot = pypot.robot.from_configuration('ergo_robot.xml')
    ergo_robot.start_sync()
    
Except from the last line, everything should be clear now. This new line starts the synchronization between your "code" robot and the real one, i.e. all commands that you will send in python code will automatically send to the physical Ergo-Robot.

Now, we are going to put the robot in its initial position::

    intial_pos = {'base_pan': 0.0,
                  'base_tilt_lower': -20.0,
                  'base_tilt_upper': 20,
                  'head_pan': 0.0,
                  'head_tilt_lower': -10,
                  'head_tilt_upper': 10}

    # we ask the robot to go to this new position in 2 seconds.
    ergo_robot.goto_position(initial_pos, 2)
    

    






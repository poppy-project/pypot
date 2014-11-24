# Pypot: A library for Dynamixel motors control #

Pypot is a framework developed in the [inria FLOWERS](https://flowers.inria.fr/) team to make it easy and fast to control custom robots based on dynamixel motors. This framework provides different levels of abstraction corresponding to different types of use. More precisely, you can use pypot to:

* directly control robotis motors through a USB2serial device,
* define the structure of your particular robot and control it through high-level commands,
* define primitives and easily combine them to create complex behavior.

Pypot has been entirely written in Python to allow for fast development, easy deployment and quick scripting by non-necessary expert developers. It can also benefits from the scientific and machine learning libraries existing in Python. The serial communication is handled through the standard library and thus allows for rather high performance (10ms sensorimotor loop). It is crossed-platform and has been tested on Linux, Windows and Mac OS.

Pypot is also compatible with the [V-REP simulator](http://www.coppeliarobotics.com). This allows you to seamlessly switch from a real robot to its simulated equivalent without having to modify your code.

## The Poppy-project: open source ##

Pypot is part of the [Poppy project](http://www.poppy-project.org) aiming at releasing an integrated humanoid platform under an open source license GPL V3. Poppy is a kid-size humanoid robot designed for biped locomotion and physical human-robot interaction. It is based on a combination of standard dynamixel actuators, 3D printed parts and open-source electronics such as Arduino boards. Both the hardware (3D models, electronics...) and software can be freely used, modified and duplicated.

Do not hesitate to contact us if you want to get involved!

## Documentation ##

The full pypot documentation on a html format can be found [here](http://poppy-project.github.io/pypot/). It provides tutorials, examples and a complete API.

## Installation ##

Before you start building pypot, you need to make sure that the following packages are already installed on your computer:

* [python](http://www.python.org) 2.7
* [pyserial](http://pyserial.sourceforge.net) 2.6 (or later)
* [numpy](http://www.numpy.org)

Once it is done, you can build and install pypot with the classical:

    cd pypot
    python setup.py install

You will also have to install the driver for the USB2serial port. There are two devices that have been tested with pypot that could be used:

* USB2AX - this device is designed to manage TTL communication only
* USB2Dynamixel - this device can manage both TTL and RS485 communication.

For more details on the installation procedure, please refer to the [installation section](http://poppy-project.github.io/pypot/intro.html#installation) of the documentation.

## Roadmap ##

The roadmap of the project can be found [here](https://github.com/poppy-project/pypot/blob/master/roadmap.md).

![Alt text](https://zenodo.org/badge/3914/poppy-project/pypot.png)

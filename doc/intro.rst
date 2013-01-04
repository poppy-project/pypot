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


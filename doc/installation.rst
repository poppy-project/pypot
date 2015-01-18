.. _installation:

Installation
============

Via Python Packages
-------------------

The pypot package is entirely written in Python. So, the install process should be rather straightforward. You can directly install it via easy_install or pip::

    pip install pypot

or::

    easy_install pypot

The up to date archive can also be directly downloaded `here <https://pypi.python.org/pypi/pypot/>`_.

From the source code
--------------------

You can also install it from the source. You can clone/fork our repo directly on `github <https://github.com/poppy-project/pypot>`_.

Before you start building pypot, you need to make sure that the following packages are already installed on your computer:

* `python <http://www.python.org>`_ 2.7 or 3
* `pyserial <http://pyserial.sourceforge.net/>`_ 2.6 (or later)
* `numpy <http://www.numpy.org>`_

Other optional packages may be installed depending on your needs:

* `sphinx <http://sphinx-doc.org/index.html>`_ (to build the doc)
* `PyQt4 <http://www.riverbankcomputing.com/software/pyqt/intro>`_ (for the graphical tools)

Once it is done, you can build and install pypot with the classical::

    cd pypot
    python setup.py build
    python setup.py install

Testing your install
--------------------

You can test if the installation went well with::

    python -c "import pypot"

You will also have to install the driver for the USB2serial port. There are two devices that have been tested with pypot that could be used:

* USB2AX - this device is designed to manage TTL communication only
* USB2Dynamixel - this device can manage both TTL and RS485 communication.

On Windows and Mac, it will be necessary to download and install a FTDI (VCP) driver to run the USB2Dynamixel, you can find it `here <http://www.ftdichip.com/Drivers/VCP.htm>`__. Linux distributions should already come with an appropriate driver. The USB2AX device should not require a driver installation under MAC or Linux, it should already exist. For Windows XP, it should automatically install the correct driver.

.. note:: On the side of the USB2Dynamixel there is a switch. This is used to select the bus you wish to communicate on. This means that you cannot control two different bus protocols at the same time.

On most Linux distributions you will not have the necessary permission to access the serial port. You can either run the command in sudo or better you can add yourself to the *dialout* group::

  sudo addgroup "username" dialout

At this point you should have a pypot ready to be used! In the extremely unlikely case where anything went wrong during the installation, please refer to the `issue tracker <https://github.com/poppy-project/pypot/issues>`_.

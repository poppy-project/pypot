.. _installation:

Installation
============
Requirements
-------------------
Pypot is written in `python <https://www.python.org/>`__ and need a python interpreter to be run. Moreover pypot has `scipy <www.scipy.org/>`_ and `numpy <http://www.numpy.org>`_ for dependencies, as they are not fully written in python they need system side packages to be build, it easier to use pre-build binaries for your operating system.

Windows
~~~~~~~~~~~~~~~~~~~
The easier way is to install `Anaconda <http://continuum.io/downloads>`_ a pre-packaged `python <https://www.python.org/>`__ distribution with lot of scientific librairies pre-compiled and a graphical installer.

After that, you can install pypot with `pip <#via-python-packages>`_ in the command prompt.

GNU/Linux
~~~~~~~~~~~~~~~~~~~
You can also install `Anaconda <http://continuum.io/downloads>`_, but it's faster to use the binaries provided by your default package manager. 

On Ubuntu & Debian::

    sudo apt-get install python-pip python-numpy python-scipy python-matplotlib

On Fedora::

    sudo yum install python-pip numpy scipy python-matplotlib
    
On Arch Linux::

    sudo pacman -S python2-pip python2-scipy python2-numpy python2-matplotlib
    
After that, you can install pypot with `pip <#via-python-packages>`_.
    
Mac OSX
~~~~~~~~~~~~~~~~~~~
Mac OSX (unlike GNU/Linux distributions) don’t come with a package manager, but there are a couple of popular package managers you can install, like `Homebrew <http://brew.sh/>`_.

The easier way is to install `Homebrew <http://brew.sh/>`_. You have to type these commands in a terminal::

    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

An use Homebrew to install python::

    brew install python
    
After that, you can install pypot with `pip <#via-python-packages>`_.


Via Python Packages
-------------------
The pypot package is entirely written in Python. So, the install process should be rather straightforward. You can directly install it via easy_install or pip::

    pip install pypot

**or**::

    easy_install pypot

The up to date archive can also be directly downloaded `here <https://pypi.python.org/pypi/pypot/>`_.

If you are on a GNU/Linux operating system, you will need to execute the above commands with **sudo**.

From the source code
--------------------

You can also install it from the source. You can clone/fork our repo directly on `github <https://github.com/poppy-project/pypot>`_.

Before you start building pypot, you need to make sure that the following packages are already installed on your computer:

* `python <http://www.python.org>`_ developed on 2.7 (also works on 3)
* `pyserial <http://pyserial.sourceforge.net/>`_ 2.6 (or later)
* `numpy <http://www.numpy.org>`_
* `scipy <www.scipy.org/>`_
* `enum34 <https://pypi.python.org/pypi/enum34>`_

Other optional packages may be installed depending on your needs:

* `sphinx <http://sphinx-doc.org/index.html>`_ and `sphinx-bootstrap-theme <http://ryan-roemer.github.io/sphinx-bootstrap-theme/>`_ (to build the doc)
* `PyQt4 <http://www.riverbankcomputing.com/software/pyqt/intro>`_ (for the graphical tools)
* `bottle <http://bottlepy.org/>`_ and `tornado <http://www.tornadoweb.org>`_ for REST API support and http-server

Once it is done, you can build and install pypot with the classical::

    cd pypot
    sudo python setup.py install

Testing your install
--------------------

You can test if the installation went well with::

    python -c "import pypot"

You will also have to install the driver for the USB2serial port. There are two devices that have been tested with pypot that could be used:

* USB2AX - this device is designed to manage TTL communication only
* USB2Dynamixel - this device can manage both TTL and RS485 communication.

On Windows and Mac, it will be necessary to download and install a FTDI (VCP) driver to run the USB2Dynamixel, you can find it `here <http://www.ftdichip.com/Drivers/VCP.htm>`__. Linux distributions should already come with an appropriate driver. The USB2AX device should not require a driver installation under MAC or Linux, it should already exist. For Windows XP, it should automatically install the correct driver.

.. note:: On the side of the USB2Dynamixel there is a switch. This is used to select the bus you wish to communicate on. This means that you cannot control two different bus protocols at the same time.

On most Linux distributions you will not have the necessary permission to access the serial port. You can either run the command in sudo or better you can add yourself to the *dialout* or the *uucp* group (depending on your distribution)::

  sudo addgroup $USER dialout
  sudo addgroup $USER uucp

At this point you should have a pypot ready to be used! In the extremely unlikely case where anything went wrong during the installation, please refer to the `issue tracker <https://github.com/poppy-project/pypot/issues>`_.

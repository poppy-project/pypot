.. _herborist:

Herborist: the configuration tool
=================================

Herborist is a graphical tool that helps you detect and configure motors before using them in your robot.

.. warning:: Herborist is entirely written in Python but requires PyQt4 to run.

More precisely, Herborist can be used to:

* Find and identify available serial ports
* Scan multiple baud rates to find all connected motors
* Modify the EEPROM configuration (of single or multiple motors)
* Make motors move (e.g. to test the angle limits).

You can directly launch herborist by running the *herborist* command in your terminal.

.. note:: When you install pypot with the setup.py, herborist is automatically added to your $PATH. You can call it from anywhere thanks to the command::

        herborist

    You can always find the script in the folder $(PYPOT_SRC)/pypot/tools/herborist.

.. image:: herborist.png
    :align: center


.. warning:: Herborist is not actively maintained and will hopefully be replaced by a better solution. So its stability is somewhat questionable.

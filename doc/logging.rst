Mastering the logging system
============================

Pypot used the Python's builtin `logging <http://docs.python.org/2/library/logging.html>`_ module for logging. For details on how to use this module please refer to Python's own documentation or the one on `django webstite <https://docs.djangoproject.com/en/1.6/topics/logging/>`_. Here, we will only describe what pypot is logging and how it is organised (see section :ref:`log_struct`). We will also present a few examples on how to use pypot logging and parse the information (see section :ref:`log_ex`).

.. _log_struct:

Logging structure
-----------------

Pypot is logging information at all different levels:

* low-level dynamixel IO
* motor and robot abstraction
* within each primitive
* each request received by the server

.. note:: As you probably do not want to log everything (pypot is sending a lot of messages!!!), you have to select in the logging structure what is relevant in your program and define it in your logging configuration.

Pypot's logging naming convention is following pypot's architecture. Here is the detail of what pypot is logging with the associated logger's name:

* The logger's name **pypot.dynamixel.io** is logging information related to opening/closing port (INFO) and each sent/received package (DEBUG). The communication and timeout error are also logged (WARNING). This logger always provides you the port name, the baudrate and timout of your connection as extra information.

* The logger **pypot.dynamixel.motor** is logging each time a register of a motor is set (DEBUG). The name of the register, the name of the motor and the set value are given in the message.

* **pypot.robot.config** is logging information regarding the creation of a robot through a config dictionary. A message is sent for each motor, controller and alias added (INFO). A WARNING message is also sent when the angle limits of a motor are changed. We provide as extra the entire config dictionary.

* The logger **pypot.robot.robot** is logging when the synchronization is started/stopped (INFO) and when a primitive is attached (INFO).

* **pypot.primitive.primitive** logs a message when the primitive is started/stopped and paused/resumed (INFO). Eeach :meth:`~pypot.primitive.primitive.LoopPrimitive.update` of a LoopPrimitive is also logged (DEBUG). Each time a primitive sets a value to a register a message is also logged (DEBUG).

* **pypot.primitive.manager** provides you information on how the values sent within primitives were combined (DEBUG).

* **pypot.server** logs when the server is started (INFO) and each handled request (DEBUG).

.. _log_ex:

Using Pypot's logging
---------------------

As an example of what you can do with the logging system, here is how you can check the "real" update frequency of a loop primitive.

First, you have to define a logging config. As you can see, here we specify that we only want the log coming form 'pypot.primitive' and the message is formatted so we only keep the timestamp::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'time': {
                'format': '%(asctime)s',
            },
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'pypot.log',
                'formatter': 'time',
            },
        },
        'loggers': {
            'pypot.primitive': {
                'handlers': ['file', ],
                'level': 'DEBUG',
            },
        },
    }

Then, we just have to write a simple program, where for instance we run our dummy primitive for ten seconds::

    import pypot.robot
    [...]

    if __name__ == '__main__':
        logging.config.dictConfig(LOGGING)

        r = pypot.robot.from_config(ergo_config)

        class DummyPrimitive(LoopPrimitive):
            pass

        p = DummyPrimitive(r, 50)
        p.start()
        time.sleep(10)
        p.stop()

The execution of the program above will create a file named 'pypot.log' where each line corresponds to the timestamp of each primitive update. This file can then be easily parsed::

    t = []

    with open('pypot.log') as f:
        for l in f.readlines():
            d = datetime.datetime.strptime('%Y-%m-%d %H:%M:%S,%f\n')
            t.append(d)

    t = numpy.array(t)
    dt = map(lambda dt: dt.total_seconds(), numpy.diff(t))
    dt = numpy.array(dt) * 1000

    print(numpy.mean(dt), numpy.std(dt))

    plot(dt)
    show()

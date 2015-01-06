Using a simulated robot with V-REP
**********************************

Connecting to V-REP
-------------------

As it is often easier to work in simulation rather than with the real robot, pypot has been linked with the `V-REP simulator <http://www.coppeliarobotics.com>`_. It is described as the "Swiss army knife among robot simulators" and is a very powerful tool to quickly (re)create robotics setup. As presenting V-REP is way beyond the scope of this tutorial, we will here assume that you are already familiar with this tool. Otherwise, you should directly refer to `V-REP documentation <http://www.coppeliarobotics.com/helpFiles/index.html>`_.

Details about how to connect pypot and V-REP can be found in `this post <https://forum.poppy-project.org/t/howto-connect-pypot-to-your-simulated-version-of-poppy-humanoid-in-v-rep/332>`_.

The connection between pypot and V-REP was designed to let you seamlessly switch from your real robot to the simulated one. It is based on `V-REP's remote API <http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm>`_.

In order to connect to V-REP through pypot, you will only need to install the `V-REP <http://www.coppeliarobotics.com/downloads.html>`_ simulator. Pypot comes with a specific :class:`~pypot.vrep.io.VrepIO` designed to communicate with V-REP through its `remote API <http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm>`_.

This IO can be used to:

* connect to the V-REP server : :class:`~pypot.vrep.io.VrepIO`
* load a scene : :meth:`~pypot.vrep.io.VrepIO.load_scene`
* start/stop/restart a simulation : :meth:`~pypot.vrep.io.VrepIO.start_simulation`, :meth:`~pypot.vrep.io.VrepIO.stop_simulation`, :meth:`~pypot.vrep.io.VrepIO.restart_simulation`
* pause/resume the simulation : :meth:`~pypot.vrep.io.VrepIO.pause_simulation`, :meth:`~pypot.vrep.io.VrepIO.resume_simulation`
* get/set a motor position : :meth:`~pypot.vrep.io.VrepIO.get_motor_position`, :meth:`~pypot.vrep.io.VrepIO.set_motor_position`
* get an object position/orienation : :meth:`~pypot.vrep.io.VrepIO.get_object_position`, :meth:`~pypot.vrep.io.VrepIO.get_object_orientation`

Switch between the simulation and the real robot in a single line of code
-------------------------------------------------------------------------

As stated above, the bridge between V-REP and pypot has been designed to let you easily switch from the robot to the simulated version. In most case, you should only have to change the way you instantiate your robot::

    # Working with the real robot
    import pypot.robot

    poppy = pypot.robot.from_config(config)

    poppy.walk.start()

will become::

    # Working with the simulated version
    import pypot.vrep

    poppy = pypot.vrep.from_vrep(config, vrep_host, vrep_port, vrep_scene)

    poppy.walk.start()

In particular, the walking primitive should work exactly the same way in both cases without needing to change anything.

.. note:: Not all dynamixel registers have their V-REP equivalent. For the moment, only the control of the position is used. More advanced features can be easily added thanks to the controller abstraction (see section :ref:`extending`).

.. _my_prim:

Primitives everywhere
=====================

In the previous sections, we have shown how to make a simple behavior thanks to the :class:`~pypot.robot.robot.Robot` abstraction. But how to combine those elementary behaviors into something more complex? You could use threads and do it manually, but we provide the :class:`~pypot.primitive.primitive.Primitive` to abstract most of the work for you.

What do we call "Primitive"?
----------------------------

We call :class:`~pypot.primitive.primitive.Primitive` any simple or complex behavior applied to a :class:`~pypot.robot.robot.Robot`. A primitive can access all sensors and effectors in the robot. A primitive is supposed to be independent of other primitives. In particular, a primitive is not aware of the other primitives running on the robot at the same time. We imagine those primitives as elementary blocks that can be combined to create more complex blocks in a hierarchical manner.

.. note:: The independence of primitives is really important when you create complex behaviors - such as balance - where many primitives are needed. Adding another primitive - such as walking - should be direct and not force you to rewrite everything. Furthermore, the balance primitive could also be combined with another behavior - such as shoot a ball - without modifying it.

To ensure this independence, the primitive is running in a sort of sandbox. More precisely, this means that the primitive has not direct access to the robot. It can only request commands (e.g. set a new goal position of a motor) to a :class:`~pypot.primitive.manager.PrimitiveManager` which transmits them to the "real" robot. As multiple primitives can run on the robot at the same time, their request orders are combined by the manager.

.. note:: The primitives all share the same manager. In further versions, we would like to move from this linear combination of all primitives to a hierarchical structure and have different layer of managers.

The manager uses a filter function to combine all orders sent by primitives. By default, this filter function is a simple mean but you can choose your own specific filter (e.g. add function).

.. warning:: You should not mix control through primitives and direct control through the :class:`~pypot.robot.robot.Robot`. Indeed, the primitive manager will overwrite your orders at its refresh frequency: i.e. it will look like only the commands send through primitives will be taken into account.

.. _write_own_prim:

Writing your own primitive
--------------------------

To write you own primitive, you have to subclass the :class:`~pypot.primitive.primitive.Primitive` class. It provides you with basic mechanisms (e.g. connection to the manager, setup of the thread) to allow you to directly "plug" your primitive to your robot and run it.

.. note:: You should always call the super constructor if you override the :meth:`~pypot.primitive.primitive.Primitive.__init__` method.

As an example, let's write a simple primitive that recreate the dance behavior written in the :ref:`dance_` section. Notice that to pass arguments to your primitive, you have to override the :meth:`~pypot.primitive.primitive.Primitive.__init__` method::

    import time

    import pypot.primitive
    class DancePrimitive(pypot.primitive.Primitive):
    
        def __init__(self, robot, amp=30, freq=0.5):
            self.robot = robot
            self.amp = amp
            self.freq = freq
            pypot.primitive.Primitive.__init__(self, robot)
        
        def run(self):
            amp = self.amp
            freq = self.freq
            # self.elapsed_time gives you the time (in s) since the primitive has been running
            while self.elapsed_time < 30:
                x = amp * numpy.sin(2 * numpy.pi * freq * self.elapsed_time)

                self.robot.base_pan.goal_position = x
                self.robot.head_pan.goal_position = -x

                time.sleep(0.02)
 
To run this primitive on your robot, you simply have to do::

    ergo_robot = pypot.robot.from_config(...)

    dance = DancePrimitive(ergo_robot,amp=60, freq=0.6)
    dance.start()
    
If you want to make the dance primitive infinite you can use the :class:`~pypot.primitive.primitive.LoopPrimitive` class::

    class LoopDancePrimitive(pypot.primitive.LoopPrimitive):
        def __init__(self, robot, refresh_freq, amp=30, freq=0.5):
            self.robot = robot
            self.amp = amp
            self.freq = freq
            LoopPrimitive.__init__(self, robot, refresh_freq)
        
        # The update function is automatically called at the frequency given on the constructor
        def update(self):
            amp = self.amp
            freq = self.freq
            x = amp * numpy.sin(2 * numpy.pi * freq * self.elapsed_time)

            self.robot.base_pan.goal_position = x
            self.robot.head_pan.goal_position = -x

And then runs it with::

    ergo_robot = pypot.robot.from_config(...)

    dance = LoopDancePrimitive(ergo_robot, 50, amp = 40, freq = 0.3)
    # The robot will dance until you call dance.stop()
    dance.start()


.. warning:: When writing your own primitive, you should always keep in mind that you should never directly pass the robot or its motors as argument and access them directly. You have to access them through the self.robot and self.robot.motors properties. Indeed, at instantiation the :class:`~pypot.robot.robot.Robot` (resp. :class:`~pypot.dynamixel.motor.DxlMotor`) instance is transformed into a :class:`~pypot.primitive.primitive.MockupRobot` (resp. :class:`~pypot.primitive.primitive.MockupMotor`). Those class are used to intercept the orders sent and forward them to the :class:`~pypot.primitive.manager.PrimitiveManager` which will combine them. By directly accessing the "real" motor or robot you circumvent this mechanism and break the sandboxing. If you have to specify a list of motors to your primitive (e.g. apply the sinusoid primitive to the specified motors), you should either give the motors name and access the motors within the primitive or transform the list of :class:`~pypot.dynamixel.motor.DxlMotor` into :class:`~pypot.primitive.primitive.MockupMotor` thanks to the :meth:`~pypot.primitive.primitive.Primitive.get_mockup_motor` method.
    For instance::

        class MyDummyPrimitive(pypot.primitive.Primitive):
            def run(self, motors_name):
                motors = [getattr(self.robot, name) for name in motors_name]

                while True:
                    for m in fake_motors:
                        ...

    or::

        class MyDummyPrimitive(pypot.primitive.Primitive):
            def run(self, motors):
                fake_motors = [self.get_mockup_motor(m) for m in motors]

                while True:
                    for m in fake_motors:
                        ...



.. _start_prim:

Start, Stop, Pause, and Resume
------------------------------

The primitive can be :meth:`~pypot.primitive.primitive.Primitive.start`, :meth:`~pypot.primitive.primitive.Primitive.stop`, :meth:`~pypot.utils.stoppablethread.StoppableThread.pause` and :meth:`~pypot.utils.stoppablethread.StoppableThread.resume`. Unlike regular python thread, primitive can be restart by calling again the :meth:`~pypot.primitive.primitive.Primitive.start` method.

When overriding the :class:`~pypot.primitive.primitive.Primitive`, you are responsible for correctly handling those events. For instance, the stop method will only trigger the should stop event that you should watch in your run loop and break it when the event is set. In particular, you should check the :meth:`~pypot.utils.stoppablethread.StoppableThread.should_stop` and :meth:`~pypot.utils.stoppablethread.StoppableThread.should_pause` in your run loop. You can also use the :meth:`~pypot.utils.stoppablethread.StoppableThread.wait_to_stop` and :meth:`~pypot.utils.stoppablethread.StoppableThread.wait_to_resume` to wait until the commands have really been executed.

.. note:: You can refer to the source code of the :class:`~pypot.primitive.primitive.LoopPrimitive` for an example of how to correctly handle all these events.


Attaching a primitive to the robot
----------------------------------

In the previous section, we explain that the primitives run in a sandbox in the sense that they are not aware of the other primitives running at the same time. In fact, this is not exactly true. More precisely, a primitive can access everything attached to the robot: e.g. motors, sensors. But you can also attach a primitive to the robot.

Let's go back on our DancePrimitive example. You can write::

    ergo_robot = pypot.robot.from_config(...)

    ergo_robot.attach_primitive(DancePrimitive(ergo_robot), 'dance')
    ergo_robot.dance.start()

By attaching a primitive to the robot, you make it accessible from within other primitive.

For instance you could then write::

    class SelectorPrimitive(pypot.primitive.Primitive):
        def run(self):
            if song == 'my_favorite_song_to_dance' and not self.robot.dance.is_alive():
                self.robot.dance.start()

.. note:: In this case, instantiating the DancePrimitive within the SelectorPrimitive would be another solution.

import sys
import time
import numpy
import threading

from collections import deque


class Primitive(object):
    """ A Primitive is an elementary behavior that can easily be combined to create more complex behaviors.

        A primitive is basically a thread with access to a "fake" robot to ensure a sort of sandboxing. More precisely, it means that the primitives will be able to:

        * request values from the real robot (motor values, sensors or attached primitives)
        * request modification of motor values (those calls will automatically be combined among all primitives by the :class:`~pypot.primitive.manager.PrimitiveManager`).

        The syntax of those requests directly match the equivalent code that you could write from the :class:`~pypot.robot.robot.Robot`. For instance you can write::

            class MyPrimitive(Primitive):
                def run(self):
                    while True:
                        for m in self.robot.motors:
                            m.goal_position = m.present_position + 10

                    time.sleep(1)

        .. warning:: In the example above, while it seems that you are setting a new goal_position, you are only requesting it. In particular, another primitive could request another goal_position and the result will be the combination of both request. For example, if you have two primitives: one setting the goal_position to 10 and the other setting the goal_position to -20, the real goal_position will be set to -5 (by default the mean of all request is used, see the :class:`~pypot.primitive.manager.PrimitiveManager` class for details).

        Primitives were developed to allow for the creation of complex behaviors such as walking. You could imagine - and this is what is actually done on the Poppy robot - having one primitive for the walking gait, another for the balance and another for handling falls.

        .. note:: This class should always be extended to define your particular behavior in the :meth:`~pypot.primitive.primitive.Primitive.run` method.

        """
    def __init__(self, robot, *args, **kwargs):
        """ At instanciation, it automatically transforms the :class:`~pypot.robot.robot.Robot`
            into a :class:`~pypot.primitive.primitive.MockupRobot`.

            :param args: the arguments are automatically passed to the run method.
            :param kwargs: the keywords arguments are automatically passed to the run method.

            .. warning:: You should not directly pass motors as argument to the primitive. If you need to, use the method :meth:`~pypot.primitive.primitive.Primitive.get_mockup_motor` to transform them into "fake" motors. See the :ref:`write_own_prim` section for details.

            """
        self.robot = MockupRobot(robot)

        self.args = args
        self.kwargs = kwargs

        self._stop = threading.Event()
        self._resume = threading.Event()

        self._synced = threading.Event()

    def _wrapped_run(self):
        self.t0 = time.time()

        self.run(*self.args, **self.kwargs)

        self._synced.wait()
        self.robot._primitive_manager.remove(self)

    def run(self, *args, **kwargs):
        """ Run method of the primitive thread. You should always overwrite this method.

            :param args: the arguments passed to the constructor are automatically passed to this method
            :param kwargs: the arguments passed to the constructor are automatically passed to this method

            .. warning:: You are responsible of handling the :meth:`~primitive.primitive.Primitive.should_stop`, :meth:`~primitive.primitive.Primitive.should_pause` and :meth:`~primitive.primitive.Primitive.wait_to_resume` methods correctly so the code inside your run function matches the desired behavior. You can refer to the code of the :meth:`~primitive.primitive.LoopPrimitive.run` method of the :class:`~primitive.primitive.LoopPrimitive` as an example.

            After termination of the run function, the primitive will automatically be removed from the list of active primitives of the :class:`~pypot.primitive.manager.PrimitiveManager`.

            """
        pass

    @property
    def elapsed_time(self):
        """ Elapsed time (in seconds) since the primitive runs. """
        return time.time() - self.t0

    # MARK: - Start/Stop handling

    def start(self):
        """ Start or restart (the :meth:`~pypot.primitive.primitive.Primitive.stop` method will automatically be called) the primitive. """
        if self.is_alive():
            self.stop()
            self.wait_to_stop()

        self._resume.set()
        self._stop.clear()
        self._synced.clear()

        self.robot._primitive_manager.add(self)

        self._thread = threading.Thread(target=self._wrapped_run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """ Requests the primitive to stop. """
        self._stop.set()

    def should_stop(self):
        """ Signals if the primitive should be stopped or not. """
        return self._stop.is_set()

    def wait_to_stop(self):
        """ Wait until the primitive actually stops. """
        if hasattr(self, '_thread'):
            self._thread.join()

    def is_alive(self):
        """ Determines whether the primitive is running or not.

            The value will be true only when the :meth:`~primitive.primitive.Primitive.run` function is executed.

            """
        return hasattr(self, '_thread') and self._thread.is_alive()

    # MARK: - Pause/Resume handling

    def pause(self):
        """ Requests the primitives to pause. """
        self._resume.clear()

    def resume(self):
        """ Requests the primitives to resume. """
        self._resume.set()

    def should_pause(self):
        """ Signals if the primitive should be paused or not. """
        return not self._resume.is_set()

    def wait_to_resume(self):
        """ Waits until the primitive is resumed. """
        self._resume.wait()

    def get_mockup_motor(self, motor):
        """ Gets the equivalent :class:`~pypot.primitive.primitive.MockupMotor`. """
        return next((m for m in self.robot.motors if m.name == motor.name), None)


class LoopPrimitive(Primitive):
    """ Simple primitive that call an update method at a predefined frequency.

        You should write your own subclass where you only defined the :meth:`~pypot.primitive.primitive.Primitive.update` method.

        """
    def __init__(self, robot, freq, *args, **kwargs):
        Primitive.__init__(self, robot, *args, **kwargs)
        self._period = 1.0 / freq
        self._recent_updates = deque([], 11)

    @property
    def recent_update_frequencies(self):
        """ Returns the 10 most recent update frequencies.

        The given frequencies are computed as short-term frequencies!
        The 0th element of the list corresponds to the most recent frequency.
        """
        return list(reversed([(1.0 / p) for p in numpy.diff(self._recent_updates)]))

    def run(self, *args, **kwargs):
        """ Calls the :meth:`~pypot.primitive.primitive.Primitive.update` method at a predefined frequency (runs until stopped). """

        while not self.should_stop():
            if self.should_pause():
                self.wait_to_resume()

            start = time.time()
            self.update(*self.args, **self.kwargs)
            end = time.time()

            self._recent_updates.append(start)

            dt = self._period - (end - start)
            if dt > 0:
                time.sleep(dt)

    def update(self, *args, **kwargs):
        """ Update methods that will be called at a predefined frequency.

            :param args: the arguments passed to the constructor are automatically passed to this method
            :param kwargs: the arguments passed to the constructor are automatically passed to this method

            """
        raise NotImplementedError


class MockupRobot(object):
    """ Fake :class:`~pypot.robot.robot.Robot` used by the :class:`~pypot.primitive.primitive.Primitive` to ensure sandboxing. """
    def __init__(self, robot):
        self._robot = robot
        self._motors = []

        for a in robot.alias:
            setattr(self, a, [])

        for m in robot.motors:
            mockup_motor = MockupMotor(m)
            self._motors.append(mockup_motor)
            setattr(self, m.name, mockup_motor)

            for a in [a for a in robot.alias if m in getattr(robot, a)]:
                getattr(self, a).append(mockup_motor)

    def __getattr__(self, attr):
        return getattr(self._robot, attr)

    def goto_position(self, position_for_motors, duration, wait=False):
        for motor_name, position in position_for_motors.iteritems():
            m = getattr(self, motor_name)
            m.goto_position(position, duration)

        if wait:
            time.sleep(duration)

    @property
    def motors(self):
        """ List of all attached :class:`~pypot.primitive.primitive.MockupMotor`. """
        return self._motors

    def power_max(self):
        for m in self.motors:
            m.compliant = False
            m.moving_speed = 0
            m.torque_limit = 100.0


class MockupMotor(object):
    """ Fake Motor used by the primitive to ensure sandboxing:

        * the read instructions are directly delegate to the real motor
        * the write instructions are stored as request waiting to be combined by the primitive manager.

        """
    def __init__(self, motor):
        object.__setattr__(self, '_m', motor)
        object.__setattr__(self, '_to_set', {})

    def __getattr__(self, attr):
        return getattr(self._m, attr)

    def __setattr__(self, attr, val):
        if attr == 'goal_speed':
            MockupMotor.goal_speed.fset(self, val)
        else:
            self._to_set[attr] = val

    def goto_position(self, position, duration, wait=False):
        """ Automatically sets the goal position and the moving speed to reach the desired position within the duration. """
        dp = abs(self.present_position - position)
        speed = (dp / float(duration)) if duration > 0 else numpy.inf
        self.moving_speed = speed
        self.goal_position = position

        if wait:
            time.sleep(duration)

    @property
    def goal_speed(self):
        """ Goal speed (in degrees per second) of the motor.

            This property can be used to control your motor in speed. Setting a goal speed will automatically change the moving speed and sets the goal position as the angle limit.

            .. note:: The motor will turn until reaching the angle limit. But this is not a wheel mode, so the motor will stop at its limits.

            """
        return numpy.sign(self.goal_position) * self.moving_speed

    @goal_speed.setter
    def goal_speed(self, value):
        if abs(value) < sys.float_info.epsilon:
            self.goal_position = self.present_position

        else:
            # 0.7 corresponds approx. to the min speed that will be converted into 0
            # and as 0 corredsponds to setting the max speed, we have to check this case
            value = numpy.sign(value) * 0.7 if abs(value) < 0.7 else value

            self.goal_position = numpy.sign(value) * self.max_pos
            self.moving_speed = abs(value)

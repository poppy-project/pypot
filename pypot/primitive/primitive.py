import sys

import numpy
import logging
import threading

from collections import deque

from ..utils import pypot_time as time

from ..utils.stoppablethread import StoppableThread, make_update_loop
from ..utils.trajectory import GotoMinJerk

logger = logging.getLogger(__name__)


class Primitive(StoppableThread):
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
    methods = ['start', 'stop', 'pause', 'resume']
    properties = []

    def __init__(self, robot):
        """ At instanciation, it automatically transforms the :class:`~pypot.robot.robot.Robot` into a :class:`~pypot.primitive.primitive.MockupRobot`.

        .. warning:: You should not directly pass motors as argument to the primitive. If you need to, use the method :meth:`~pypot.primitive.primitive.Primitive.get_mockup_motor` to transform them into "fake" motors. See the :ref:`write_own_prim` section for details.

        """
        StoppableThread.__init__(self,
                                 setup=self._prim_setup,
                                 target=self._prim_run,
                                 teardown=self._prim_teardown)

        self.robot = MockupRobot(robot)

        self._synced = threading.Event()

    def _prim_setup(self):
        logger.info("Primitive %s setup.", self)

        for m in self.robot.motors:
            m._to_set.clear()

        self.robot._primitive_manager.add(self)
        self.setup()

        self.t0 = time.time()

    def setup(self):
        """ Setup methods called before the run loop.

        You can override this method to setup the environment needed by your primitive before the run loop. This method will be called every time the primitive is started/restarted.
        """
        pass

    def _prim_run(self):
        self.run()

    def run(self):
        """ Run method of the primitive thread. You should always overwrite this method.

        .. warning:: You are responsible of handling the :meth:`~pypot.utils.stoppablethread.StoppableThread.should_stop`, :meth:`~pypot.utils.stoppablethread.StoppableThread.should_pause` and :meth:`~pypot.utils.stoppablethread.StoppableThread.wait_to_resume` methods correctly so the code inside your run function matches the desired behavior. You can refer to the code of the :meth:`~pypot.utils.stoppablethread.StoppableLoopThread.run` method of the :class:`~pypot.primitive.primitive.LoopPrimitive` as an example.

        After termination of the run function, the primitive will automatically be removed from the list of active primitives of the :class:`~pypot.primitive.manager.PrimitiveManager`.

        """
        pass

    def _prim_teardown(self):
        logger.info("Primitive %s teardown.", self)
        self.teardown()

        # Forces a last synced to make sure that all values sent
        # Within the primitives will be sent to the motors.
        self._synced.clear()
        self._synced.wait()

        self.robot._primitive_manager.remove(self)

    def teardown(self):
        """ Tear down methods called after the run loop.

        You can override this method to clean up the environment needed by your primitive. This method will be called every time the primitive is stopped.

        """
        pass

    @property
    def elapsed_time(self):
        """ Elapsed time (in seconds) since the primitive runs. """
        return time.time() - self.t0

    # MARK: - Start/Stop handling
    def start(self):
        """ Start or restart (the :meth:`~pypot.primitive.primitive.Primitive.stop` method will automatically be called) the primitive. """
        if not self.robot._primitive_manager.running:
            raise RuntimeError('Cannot run a primitive when the sync is stopped!')

        StoppableThread.start(self)
        self.wait_to_start()

        logger.info("Primitive %s started.", self)

    def stop(self, wait=True):
        """ Requests the primitive to stop. """
        logger.info("Primitive %s stopped.", self)
        StoppableThread.stop(self, wait)

    def is_alive(self):
        """ Determines whether the primitive is running or not.

        The value will be true only when the :meth:`~pypot.utils.stoppablethread.StoppableThread.run` function is executed.

        """
        return self.running

    def get_mockup_motor(self, motor):
        """ Gets the equivalent :class:`~pypot.primitive.primitive.MockupMotor`. """
        return next((m for m in self.robot.motors if m.name == motor.name), None)

    # Utility function to try to help to better control
    # the synchronization and merging process of primitives
    # This is clearly a patch before a better definition of primitives.

    @property
    def being_synced(self):
        return self.robot._primitive_manager.syncing

    def affect_once(self, motor, register, value):
        with self.being_synced:
            setattr(motor, register, value)

        self._synced.clear()
        self._synced.wait()

        del motor._to_set[register]


class LoopPrimitive(Primitive):
    """ Simple primitive that call an update method at a predefined frequency.

        You should write your own subclass where you only defined the :meth:`~pypot.primitive.primitive.LoopPrimitive.update` method.

        """
    def __init__(self, robot, freq):
        Primitive.__init__(self, robot)
        # self._period = 1.0 / freq
        self.period = 1.0 / freq
        self._recent_updates = deque([], 11)

    @property
    def recent_update_frequencies(self):
        """ Returns the 10 most recent update frequencies.

        The given frequencies are computed as short-term frequencies!
        The 0th element of the list corresponds to the most recent frequency.
        """
        return list(reversed([(1.0 / p) for p in numpy.diff(self._recent_updates)]))

    def run(self):
        """ Calls the :meth:`~pypot.utils.stoppablethread.StoppableLoopThread.update` method at a predefined frequency (runs until stopped). """
        make_update_loop(self, self._wrapped_update)

    def _wrapped_update(self):
        logger.debug('LoopPrimitive %s updated.', self)
        self._recent_updates.append(time.time())
        self.update()

    def update(self):
        """ Update methods that will be called at a predefined frequency. """
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

    def goto_position(self, position_for_motors, duration, control=None, wait=False):
        for i, (motor_name, position) in enumerate(position_for_motors.iteritems()):
            w = False if i < len(position_for_motors) - 1 else wait

            m = getattr(self, motor_name)
            m.goto_position(position, duration, control, wait=w)

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
            logger.debug("Setting MockupMotor '%s.%s' to %s",
                         self.name, attr, val)

    def goto_position(self, position, duration, control=None, wait=False):
        """ Automatically sets the goal position and the moving speed to reach the desired position within the duration. """

        if control is None:
            control = self.goto_behavior

        if control == 'minjerk':
            goto_min_jerk = GotoMinJerk(self, position, duration)
            goto_min_jerk.start()
            if wait:
                goto_min_jerk.wait_to_stop()

        elif control == 'dummy':
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

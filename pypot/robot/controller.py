from ..utils.stoppablethread import StoppableLoopThread


class AbstractController(StoppableLoopThread):
    """ Abstract class for motor/sensor controller.

    The controller role is to synchronize the reading/writing of a set of instances with their "hardware" equivalent through an :class:`~pypot.robot.io.AbstractIO` object. It is defined as a :class:`~pypot.utils.stoppablethread.StoppableLoopThread` where each loop update synchronizes  values from the "software" objects with their "hardware" equivalent.

    To define your Controller, you need to define the :meth:`~pypot.utils.stoppablethread.StoppableLoopThread.update` method. This method will be called at the predefined frequency. An exemple of how to do it can be found in :class:`~pypot.dynamixel.controller.BaseDxlController`.

    """
    def __init__(self, io, sync_freq):
        """
        :param io: IO used to communicate with the hardware motors
        :type io: :class:`~pypot.robot.io.AbstractIO`
        :param float sync_freq: synchronization frequency

        """
        StoppableLoopThread.__init__(self, sync_freq)

        self.io = io

    def start(self):
        StoppableLoopThread.start(self)
        self.wait_to_start()

    def close(self):
        """ Cleans and closes the controller. """
        self.stop()

        if self.io is not None:
            self.io.close()


class MotorsController(AbstractController):
    """ Abstract class for motors controller.

    The controller synchronizes the reading/writing of a set of motor instances with their "hardware". Each update loop synchronizes values from the "software" :class:`~pypot.dynamixel.motor.DxlMotor` with their "hardware" equivalent.

    """
    def __init__(self, io, motors, sync_freq=50):
        """
        :param io: IO used to communicate with the hardware motors
        :type io: :class:`~pypot.robot.io.AbstractIO`
        :param list motors: list of motors attached to the controller
        :param float sync_freq: synchronization frequency

        """
        AbstractController.__init__(self, io, sync_freq)

        self.motors = motors


class DummyController(MotorsController):
    def __init__(self, motors):
        MotorsController.__init__(self, None, motors)

    def setup(self):
        for m in self.motors:
            m.goal_position = 0.0

    def update(self):
        for m in self.motors:
            m.__dict__['present_position'] = m.__dict__['goal_position']


class SensorsController(AbstractController):
    """ Abstract class for sensors controller.

    The controller frequently pulls new data from a "real" sensor and updates its corresponding software instance.

    """
    def __init__(self, io, sensors, sync_freq=50.):
        """
        :param io: IO used to communicate with the hardware motors
        :type io: :class:`~pypot.robot.io.AbstractIO`
        :param list sensors: list of sensors attached to the controller
        :param float sync_freq: synchronization frequency

        """
        AbstractController.__init__(self, io, sync_freq)

        self.sensors = sensors

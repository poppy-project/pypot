from ..utils.stoppablethread import StoppableLoopThread


class AbstractController(StoppableLoopThread):
    """ Abstract class for motors controller.

    The controller role is to synchronize the reading/writing of a set of motor instances with their "hardware" equivalent through an :class:`~pypot.robot.io.AbstractIO` object. It is defined as a :class:`~pypot.utils.stoppablethread.StoppableLoopThread` where each loop update synchronizes  values from the "software" :class:`~pypot.dynamixel.motor.DxlMotor` with their "hardware" equivalent.

    To define your Controller, you need to define the :meth:`~pypot.utils.stoppablethread.StoppableLoopThread.update` method. This method will be called at the predefined frequency. An exemple of how to do it can be found in :class:`~pypot.dynamixel.controller.BaseDxlController`.

    """
    def __init__(self, io, motors, sync_freq=50.):
        """
        :param io: IO used to communicate with the hardware motors
        :type io: :class:`~pypot.robot.io.AbstractIO`
        :param list motors: list of motors attached to the controller
        :param float sync_freq: synchronization frequency

        """
        StoppableLoopThread.__init__(self, sync_freq)

        self.io = io
        self.motors = motors

    def close(self):
        """ Cleans and closes the controller. """
        self.stop()
        self.io.close()

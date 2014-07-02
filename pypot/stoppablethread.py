import threading
import time

from abc import ABCMeta, abstractmethod


class StoppableThread(object):
    __metaclass__ = ABCMeta

    """ Stoppable version of python Thread.

    This class provides the following mechanism on top of "classical" python Thread:
        * you can stop the thread (if you defined your run method accordingly).
        * you can restart a thread (stop it and re-run it)

    .. warning:: It is up to the subclass to correctly respond to the stop signal (see :meth:`~pypot.stoppablethread.StoppableThread.run` for details).

    """
    def __init__(self):
        self._started = threading.Event()
        self._running = threading.Event()

    def start(self):
        """ Start the run method as a new thread.

        It will first stop the thread if it is already running.

        """
        if self.running:
            self.stop()

        self._thread = threading.Thread(target=self._wrapped_target)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """ Stop the thread.

        More precisely, sends the stopping signal to the thread. It is then up top the run method to correctly responds.

         """
        if self.started:
            self._running.clear()
            self._thread.join()
            self._started.clear()

    def join(self):
        """ Wait for the thread termination. """
        if not self.started:
            raise RuntimeError('cannot join thread before it is started')
        self._thread.join()

    @property
    def running(self):
        """ Whether the thread is running. """
        return self._running.is_set()

    @property
    def started(self):
        """ Whether the thread has been started. """
        return self._started.is_set()

    def wait_for_start(self):
        self._started.wait()

    def setup(self):
        """ Setup method call just before the run. """
        pass

    @abstractmethod
    def run(self):
        """ Run method of the thread.

        .. warning:: In order to be stoppable, this method has to check the running property - as often as possible to improve responsivness - and terminate when running become False. For instance, this can be implemented as follows:

            while self.running:
                do_atom_work()
                ...

        """
        pass

    def teardown(self):
        """ Teardown method call just after the run. """
        pass

    def _wrapped_target(self):
        self.setup()

        self._started.set()

        self._running.set()
        self.run()
        self._running.clear()

        self.teardown()


class StoppableLoopThread(StoppableThread):
    """ LoopThread calling an update method at a pre-defined frequency.

    .. note:: This class does not mean to be accurate. The given frequency will be approximately followed - depending for instance on CPU load - and only reached if the update method takes less time than the chosen loop period.

    """
    __metaclass__ = ABCMeta

    def __init__(self, frequency):
        """
        :params float frequency: called frequency of the :meth:`~pypot.stoppablethread.StoppableLoopThread.update` method

        """
        StoppableThread.__init__(self)

        self.period = 1.0 / frequency

    def run(self):
        """ Called the update method at the pre-defined frequency. """
        while self.running:
            start = time.time()
            self.update()
            end = time.time()

            dt = self.period - (end - start)
            if dt > 0:
                time.sleep(dt)

    @abstractmethod
    def update(self):
        """ Update method called at the pre-defined frequency. """
        pass

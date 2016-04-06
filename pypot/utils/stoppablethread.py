import threading

from . import pypot_time as time


class StoppableThread(object):
    """ Stoppable version of python Thread.

    This class provides the following mechanism on top of "classical" python Thread:
        * you can stop the thread (if you defined your run method accordingly).
        * you can restart a thread (stop it and re-run it)
        * you can pause/resume a thread

    .. warning:: It is up to the subclass to correctly respond to the stop, pause/resume signals (see :meth:`~pypot.utils.stoppablethread.StoppableThread.run` for details).

    """
    def __init__(self, setup=None, target=None, teardown=None):
        """
        :param func setup: specific setup function to use (otherwise self.setup)
        :param func target: specific target function to use (otherwise self.run)
        :param func teardown: specific teardown function to use (otherwise self.teardown)

        """
        self._started = threading.Event()
        self._running = threading.Event()
        self._resume = threading.Event()

        self._setup = self.setup if setup is None else setup
        self._target = self.run if target is None else target
        self._teardown = self.teardown if teardown is None else teardown
        self._crashed = False

    def start(self):
        """ Start the run method as a new thread.

        It will first stop the thread if it is already running.

        """
        if self.running:
            self.stop()

        self._thread = threading.Thread(target=self._wrapped_target)
        self._thread.daemon = True
        self._thread.start()

    def stop(self, wait=True):
        """ Stop the thread.

        More precisely, sends the stopping signal to the thread. It is then up to the run method to correctly responds.

        """
        if self.started:
            self._running.clear()
            self._resume.set()

            # We cannot wait for ourself
            if wait and (threading.current_thread() != self._thread):
                self._thread.join()

            self._started.clear()
            self._resume.clear()

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

    def wait_to_start(self, allow_failure=False):
        """ Wait for the thread to actually starts. """
        self._started.wait()

        if self._crashed and not allow_failure:
            self._thread.join()
            raise RuntimeError('Setup failed, see {} Traceback'
                               'for details.'.format(self._thread.name))

    def should_stop(self):
        """ Signals if the thread should be stopped or not. """
        return not self.running

    def wait_to_stop(self):
        """ Wait for the thread to terminate. """
        if not self.started:
            self.wait_to_start()
        self.join()

    def setup(self):
        """ Setup method call just before the run. """
        pass

    def run(self):
        """ Run method of the thread.

        .. note:: In order to be stoppable (resp. pausable), this method has to check the running property - as often as possible to improve responsivness - and terminate when :meth:`~pypot.utils.stoppablethread.StoppableThread.should_stop` (resp. :meth:`~pypot.utils.stoppablethread.StoppableThread.should_pause`) becomes True.
            For instance::

                while self.should_stop():
                    do_atom_work()
                    ...

        """
        pass

    def teardown(self):
        """ Teardown method call just after the run. """
        pass

    def _wrapped_target(self):
        try:
            self._setup()

            self._started.set()
            self._resume.set()

            self._running.set()
            self._target()
            self._running.clear()

            self._teardown()
        # In case something goes wrong within the thread
        # we try/catch the exceptions
        # clear all Condition locks (to avoid blocking main thread)
        # and re-raise exception for backtrace
        except:
            self._crashed = True
            self._started.set()
            self._running.clear()
            self._resume.clear()
            raise

    def should_pause(self):
        """ Signals if the thread should be paused or not. """
        return self.paused

    @property
    def paused(self):
        return not self._resume.is_set()

    def pause(self):
        """ Requests the thread to pause. """
        self._resume.clear()

    def resume(self):
        """ Requests the thread to resume. """
        self._resume.set()

    def wait_to_resume(self):
        """ Waits until the thread is resumed. """
        self._resume.wait()


def make_update_loop(thread, update_func):
    """ Makes a run loop which calls an update function at a predefined frequency. """
    while not thread.should_stop():
        if thread.should_pause():
            thread.wait_to_resume()

        start = time.time()
        if hasattr(thread, '_updated'):
            thread._updated.clear()
        update_func()
        if hasattr(thread, '_updated'):
            thread._updated.set()
        end = time.time()

        dt = thread.period - (end - start)

        if dt > 0:
            time.sleep(dt)


class StoppableLoopThread(StoppableThread):
    """ LoopThread calling an update method at a pre-defined frequency.

    .. note:: This class does not mean to be accurate. The given frequency will be approximately followed - depending for instance on CPU load - and only reached if the update method takes less time than the chosen loop period.

    """
    def __init__(self, frequency, update=None):
        """
        :params float frequency: called frequency of the :meth:`~pypot.stoppablethread.StoppableLoopThread.update` method

        """
        StoppableThread.__init__(self)

        self.period = 1.0 / frequency
        self._update = self.update if update is None else update
        self._updated = threading.Event()

    def run(self):
        """ Called the update method at the pre-defined frequency. """
        make_update_loop(self, self._update)

    def update(self):
        """ Update method called at the pre-defined frequency. """
        pass

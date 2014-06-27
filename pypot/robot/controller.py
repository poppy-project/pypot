import threading

from abc import ABCMeta, abstractmethod


class AbstractController(object):
    __metaclass__ = ABCMeta

    def __init__(self, io, motors, sync_freq=50.):
        """ """
        self.io = io
        self._motors = motors

        self._sync_period = 1.0 / sync_freq
        self._running = threading.Event()

    def start(self):
        """ """
        if self.running():
            self.stop(wait=True)

        self._running.set()
        self._sync_thread = threading.Thread(target=self.sync_values)
        self._sync_thread.start()

    def stop(self):
        """ """
        if not self.running():
            return

        self._running.clear()
        self._sync_thread.join()

    def close(self):
        """ """
        self.stop()
        self.io.close()

    def running(self):
        return self._running.is_set()

    @abstractmethod
    def sync_values(self):
        pass

    @property
    def motors(self):
        return self._motors

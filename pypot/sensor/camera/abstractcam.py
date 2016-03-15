import time

from threading import Thread

from ...robot.sensor import Sensor


class AbstractCamera(Sensor):
    registers = Sensor.registers + ['frame', 'resolution', 'fps']

    def __init__(self, name, resolution, fps):
        Sensor.__init__(self, name)

        self._res, self._fps = resolution, fps
        self._last_frame = self._grab_and_process()

        self.running = True
        self._processing = Thread(target=self._process_loop)
        self._processing.daemon = True
        self._processing.start()

    @property
    def frame(self):
        return self._last_frame

    def post_processing(self, image):
        return image

    def grab(self):
        raise NotImplementedError

    def _grab_and_process(self):
        return self.post_processing(self.grab())

    def _process_loop(self):
        period = 1.0 / self.fps

        while self.running:
            self._last_frame = self._grab_and_process()
            time.sleep(period)

    @property
    def resolution(self):
        return list(reversed(self.frame.shape[:2]))

    @property
    def fps(self):
        return self._fps

    def close(self):
        self.running = False
        self._processing.join()

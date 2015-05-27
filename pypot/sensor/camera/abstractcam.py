from ...robot.sensor import Sensor


class AbstractCamera(Sensor):
    registers = Sensor.registers + ['frame', 'resolution', 'fps']

    def __init__(self, name, resolution, fps):
        Sensor.__init__(self, name)

        self._res, self._fps = resolution, fps

    @property
    def frame(self):
        frame = self.grab()
        return self.post_processing(frame)

    def post_processing(self, image):
        return image

    def grab(self):
        raise NotImplementedError

    @property
    def resolution(self):
        return self._res

    @property
    def fps(self):
        return self._fps

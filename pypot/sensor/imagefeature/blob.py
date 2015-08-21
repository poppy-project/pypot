import cv2

from numpy import ones, uint8, concatenate

from ...robot.controller import SensorsController
from ...robot.sensor import Sensor


class Blob(Sensor):
    registers = Sensor.registers + ['center', 'radius']

    def __init__(self, x, y, radius):
        self.center = x, y
        self.radius = radius

    def draw(self, img, color=(255, 0, 0), thickness=3):
        cv2.circle(img, self.center, self.radius, color, thickness)

    @property
    def json(self):
        return {"center": self.center, "radius": self.radius}


class BlobDetector(SensorsController):
    channels = {
        'R': 2, 'G': 1, 'B': 0,
        'H': 0, 'S': 1, 'V': 2
    }

    def __init__(self, robot, name, cameras, freq, filters):
        SensorsController.__init__(self, None, [], freq)

        self.name = name

        self._robot = robot
        self._names = cameras
        self._blobs = []
        self.filters = filters

    def detect_blob(self, img, filters):
        """
            "filters" must be something similar to:
            filters = {
                'R': (150, 255), # (min, max)
                'S': (150, 255),
            }

        """
        acc_mask = ones(img.shape[:2], dtype=uint8) * 255

        rgb = img.copy()
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        for c, (min, max) in filters.items():
            img = rgb if c in 'RGB' else hsv

            mask = img[:, :, self.channels[c]]
            mask[mask < min] = 0
            mask[mask > max] = 0

            acc_mask &= mask

        kernel = ones((5, 5), uint8)
        acc_mask = cv2.dilate(cv2.erode(acc_mask, kernel), kernel)

        circles = cv2.HoughCircles(acc_mask, cv2.HOUGH_GRADIENT, 3, img.shape[0] / 5.)
        return circles.reshape(-1, 3) if circles is not None else []

    def update(self):
        if not hasattr(self, 'cameras'):
            self.cameras = [getattr(self._robot, c) for c in self._names]

        self._blobs = concatenate([self.detect_blob(c.frame, self.filters)
                                   for c in self.cameras])

    @property
    def blobs(self):
        return [Blob(*b) for b in self._blobs]

    @property
    def registers(self):
        return ['blobs']

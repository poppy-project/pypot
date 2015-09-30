import cv2

from numpy import mean, concatenate

from ...robot.controller import SensorsController
from ...robot.sensor import Sensor


class Face(Sensor):
    registers = Sensor.registers + ['center', 'rect']

    def __init__(self, rect):
        x, y, w, h = rect
        self.center = mean([[x, x + w], [y, y + h]], axis=1)
        self.rect = rect

    def draw(self, img, color=(255, 0, 0), thickness=3):
        x, y, w, h = self.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness)

    @property
    def json(self):
        return {"center": self.center, "rect": self.rect}


class FaceDetector(SensorsController):
    def __init__(self, robot, name, cameras, freq,
                 cascade='/home/coyote/dev/opencv-3.0.0/data/haarcascades/haarcascade_frontalface_alt.xml'):
        SensorsController.__init__(self, None, [], freq)

        self.name = name

        self._robot = robot
        self._names = cameras
        self._faces = []

        self.cascade = cv2.CascadeClassifier(cascade)

    def detect_face(self, img):
        rects = self.cascade.detectMultiScale(img, scaleFactor=1.3,
                                              minNeighbors=4,
                                              minSize=(20, 20))
        return rects

    def update(self):
        if not hasattr(self, 'cameras'):
            self.cameras = [getattr(self._robot, c) for c in self._names]

        self._faces = concatenate([self.detect_face(c.frame) for c in self.cameras])

    @property
    def faces(self):
        return [Face(f) for f in self._faces]

    @property
    def registers(self):
        return ['faces']

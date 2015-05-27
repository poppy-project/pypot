import cv2

from .abstractcam import AbstractCamera


class OpenCVCamera(AbstractCamera):
    registers = AbstractCamera.registers + ['index']

    def __init__(self, name, index, resolution, fps):
        AbstractCamera.__init__(self, name, resolution, fps)

        self._index = index
        self.capture = cv2.VideoCapture(self.index)
        if not self.capture.isOpened():
            raise ValueError('Can not open camera device {}!'.format(index))

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    @property
    def index(self):
        return self._index

    def grab(self):
        rval, frame = self.capture.read()
        if not rval:
            raise EnvironmentError('Can not grab image from the camera!')

        return frame

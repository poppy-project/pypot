import time

from picamera.array import PiRGBArray
from picamera import PiCamera

from .abstractcam import AbstractCamera


class RPiCamera(AbstractCamera):
    def __init__(self, name, resolution, fps):
        AbstractCamera.__init__(self, name, resolution, fps)

        cam = PiCamera()
        cam.resolution = resolution
        cam.framerate = fps

        self._cap = PiRGBArray(cam, size=resolution)

        time.sleep(0.1)

        self._frame_it = cam.capture_continuous(self._cap, format="bgr",
                                                use_video_port=True)

    @property
    def index(self):
        return self._index

    def grab(self):
        frame = self._frame_it.next().array
        self._cap.truncate(0)

        return frame

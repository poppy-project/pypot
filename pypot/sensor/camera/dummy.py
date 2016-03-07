import numpy

from .abstractcam import AbstractCamera


class DummyCamera(AbstractCamera):
    def __init__(self, name, resolution, fps, **extra):
        AbstractCamera.__init__(self, name, resolution, fps)

    def grab(self):
        if not hasattr(self, '_frame'):
            self._frame = numpy.zeros(list(self._res) + [3], dtype=numpy.uint8)

        return self._frame

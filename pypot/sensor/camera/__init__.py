from ...robot.controller import SensorsController


class CameraController(SensorsController):
    def __init__(self, camera):
        SensorsController.__init__(self, None, [camera], sync_freq=1.)


try:
    from .opencvcam import OpenCVCamera
except ImportError:
    pass

from multiprocessing import Process, Queue

from hampy import detect_markers

from ...robot.controller import SensorsController
from ...robot.sensor import Sensor


class Marker(Sensor):
    registers = Sensor.registers + ['position', 'id']

    def __init__(self, marker):
        Sensor.__init__(self, 'marker_{}'.format(marker.id))

        self.position = marker.normalized_center
        self.id = marker.id

        self._marker = marker

    def __getattr__(self, attr):
        return getattr(self._marker, attr)

    @property
    def json(self):
        return {"id": self.id, "position": self.position}


class MarkerDetector(SensorsController):
    def __init__(self, robot, name, cameras, freq, multiprocess=True):
        SensorsController.__init__(self, None, [], freq)

        self.name = name

        self._robot = robot
        self._names = cameras

        self.detect = (lambda img: self._bg_detection(img)
                       if multiprocess else detect_markers(img))

    def update(self):
        if not hasattr(self, 'cameras'):
            self.cameras = [getattr(self._robot, c) for c in self._names]

        self._markers = sum([self.detect(c.frame) for c in self.cameras], [])
        self.sensors = [Marker(m) for m in self._markers]

    @property
    def markers(self):
        return self.sensors

    @property
    def registers(self):
        return ['markers']

    def _detect(self, q, img):
        q.put(detect_markers(img))

    def _bg_detection(self, img):
        if not hasattr(self, 'q'):
            self.q = Queue()

        p = Process(target=self._detect, args=(self.q, img))
        p.start()
        return self.q.get()

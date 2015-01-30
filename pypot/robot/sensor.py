from numpy import array, zeros


class Sensor(object):
    """ Purely abstract class representing any sensor object. """
    registers = []

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class ObjectTracker(Sensor):
    registers = Sensor.registers + ['position', 'orientation']

    def __init__(self, name):
        Sensor.__init__(self, name)

        self._pos = zeros(3)
        self._ori = zeros(3)

    @property
    def position(self):
        return self._pos

    @position.setter
    def position(self, new_pos):
        self._pos = array(new_pos)

    @property
    def orientation(self):
        return self._pos

    @orientation.setter
    def orientation(self, new_ori):
        self._ori = array(new_ori)

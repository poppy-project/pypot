from __future__ import print_function, division

import time
import numpy

from collections import deque

from ...robot.sensor import Sensor
from ...utils import StoppableLoopThread
from ...utils.i2c_controller import I2cController


class SonarSensor(Sensor):
    """ Give acces to ultrasonic I2C modules SRF-02 in a *pypot way*

        It provides one register: distance (in meters).

    """
    registers = Sensor.registers + ['distance']

    def __init__(self, name, i2c_pin, address, sync_freq=50.0):
        Sensor.__init__(self, name)

        self._d = numpy.nan

        self._sonar = Sonar(i2c_pin, [address])

        self._controller = StoppableLoopThread(sync_freq, update=self.update)
        self._controller.start()

    def close(self):
        self._controller.stop()

    def update(self):
        self._sonar.update()
        self.distance = self._sonar.data[0]

    @property
    def distance(self):
        return self._d

    @distance.setter
    def distance(self, d):
        self._d = d / 100


class Sonar(object):
    """ Give acces to ultrasonic I2C modules SRF-02 connected with I2C pin of your board.
        To get more information, go to http://www.robot-electronics.co.uk/htm/srf02techI2C.htm

        Example:

        > i2c = smbus.SMBus(1)
        > sonar = Sonar(i2c, addresses=[0x70, 0x71, 0x72])
        >
    """

    def __init__(self, pin_number, addresses=[0x70]):
        """ 0x70 is the default address for the SRF-02 I2C module. """

        self.i2c = I2cController(pin_number)
        self.addresses = addresses

        self.data = None

        self._raw_data_queues = [deque([], 5) for _ in addresses]

        self.results_type = {'inches': 0x50,
                             'centimeters': 0x51,
                             'microseconds': 0x52}

        self.__errors = 0

    def update(self):
        self.ping()
        time.sleep(0.065)
        self.data = self._filter(self.read())
        return self.data

    def ping(self):
        for addr in self.addresses:
            self._ping(addr)

    def read(self, reg=2):
        return [self._read(addr, reg) for addr in self.addresses]

    def _filter(self, data):
        """ Apply a filter to reduce noisy data.

           Return the median value of a heap of data.

        """
        filtered_data = []
        for queue, data in zip(self._raw_data_queues, data):
            queue.append(data)
            filtered_data.append(numpy.median(queue))

        return filtered_data

    def _ping(self, address, data=None):
        d = data if data is not None else self.results_type['centimeters']

        while True:
            try:
                self.i2c.write_byte_data(address, 0, d)
                break
            except IOError:
                time.sleep(0.005)
                self.__errors += 1

    def _read(self, address, reg=2):
        while True:
            try:
                return int(self.i2c.read_word_data(address, reg)) / 256
            except IOError:
                time.sleep(0.005)
                self.__errors += 1


if __name__ == '__main__':
    import smbus

    from pylab import plot

    i2c = smbus.SMBus(1)
    sonar = Sonar(i2c)

    d = []
    t = [time.time()]
    for _ in range(1000):
        sonar.update()
        d.append(sonar.data[0])
        t.append(time.time() - t[0])
    plot(t[1:], d)

import serial
import json

from ...robot.sensor import Sensor
from ...utils import StoppableLoopThread


class ArduinoSensor(Sensor):
    """ Give acces to arduino sensor.

        Be careful to set the sync_freq of your controller faster than the data comes from your arduino.
        If not, you won't be able to retrieve the more recent data.

    """
    def __init__(self, name, port, baud, sync_freq=50.0):
        Sensor.__init__(self, name)
        self.port = port
        self.baud = baud
        self._controller = StoppableLoopThread(sync_freq, update=self.update)

    def start(self):
        self._ser = serial.Serial(self.port, self.baud)
        self._controller.start()

    def close(self):
        self._controller.stop()
        self._ser.close()

    def update(self):
        while self._ser.inWaiting() > 0:
            line = self._ser.readline()
        try:
            self.sensor_dict = json.loads(line)
        except json.JSONDecodeError:
            pass

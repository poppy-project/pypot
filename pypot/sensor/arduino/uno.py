import serial
import json

from ...robot.sensor import Sensor
from ...utils import StoppableLoopThread


class ArduinoSensor(Sensor):
    """ Give acces to arduino sensor.

        Here it is an example of the arduino code to retrieve the time:

        unsigned long time;
        void setup() {
            Serial.begin(1000000);
        }
        void loop() {
            // prints fixed data in json format
            Serial.print("{\"Day\":\"monday\",");
            Serial.print("\"Time\":");
            time = millis();
            // prints time since program started
            Serial.print(time);
            Serial.println("}");
            // wait 20 ms to send the data at 50 Hz
            delay(0.02);
        }

        Be careful to not set the sync_freq of your controller slower than the data comes from your arduino (here 50 Hz).

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

import Adafruit_DHT

from ...robot.sensor import Sensor


class HumiditySensor(Sensor):
    """this class give access to humidity sensor"""
    registers = Sensor.registers + ['sensor_type', 'humidity', 'temperature']

    def __init__(self, name, sensor_type, gpio_number, humidity_offset,
                 temperature_offset):
        Sensor.__init__(self, name)
        sensor_args = {'DHT11': Adafruit_DHT.DHT11,
                       'DHT22': Adafruit_DHT.DHT22,
                       'AM2302': Adafruit_DHT.AM2302}

        # Sensor should be set to DHT11, DHT22, or AM2302.
        self._sensor, self._pin = sensor_args[sensor_type], gpio_number

        self._humidity_offset = humidity_offset
        self._temperature_offset = temperature_offset

        self._humidity = 0
        self._temperature = 0

    @property
    def sensor_type(self):
        return self.sensor

    @property
    def humidity(self):
        return self._humidity

    @property
    def temperature(self):
        return self._temperature

    def get_data(self):
        # Try to grab a sensor reading.
        # Use the read_retry method which will retry up to 15 times to get a
        # sensor reading (waiting 2 seconds between each retry).
        self._humidity, self._temperature = Adafruit_DHT.read_retry(
            self._sensor, self._pin)

        while self._humidity > 100.0:
            time.sleep(2)
            self._humidity, self._temperature = Adafruit_DHT.read_retry(
                                                self._sensor, self._pin)

        self._humidity = self._humidity + self._humidity_offset
        self._temperature = self._temperature + self._temperature_offset
        return self._temperature, self._humidity

    def calibration(self, realTemperature, realHumidity):
        # Here we catch real temperature given by user to evaluate delta
        # between real life and measure from the sensor.
        self.get_data()
        self._humidity_offset = self._humidity_offset + (
            realHumidity - self._humidity)
        self._temperature_offset = self._temperature_offset + (
            realTemperature - self._temperature)
        print 'Temp offset={0:0.1f}*C  Humidity offset={1:0.1f}%'.format(
            self._temperature_offset, self._humidity_offset)
        return self._temperature_offset, self.self._humidity_offset

import RPi.GPIO as GPIO

from ...robot.sensor import Sensor


class ContactSensor(Sensor):
    """ Gives access to a micro switch sensor. """
    registers = Sensor.registers + ['contact']

    def __init__(self, name, gpio_data, gpio_vcc=None):
        Sensor.__init__(self, name)

        self._pin = gpio_data
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._pin, GPIO.IN)

        if gpio_vcc is not None:
            self._vcc = gpio_vcc
            GPIO.setup(self._vcc, GPIO.OUT)
            GPIO.output(self._vcc, GPIO.HIGH)

    @property
    def contact(self):
        return GPIO.input(self._pin) != 0

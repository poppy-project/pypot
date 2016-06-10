import RPi.GPIO as GPIO

from ...robot.sensor import Sensor


class ContactSensor(Sensor):
    """ this class gives access to a contact sensor """
    registers = Sensor.registers + ['contact']

    def __init__(self, name, gpio_number):
        Sensor.__init__(self, name)

        self._pin = gpio_number

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._pin, GPIO.IN)

    @property
    def contact(self):
        return GPIO.input(self._pin)

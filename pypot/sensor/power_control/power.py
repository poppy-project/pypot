import RPi.GPIO as GPIO

from ...robot.sensor import Sensor


class PowerContactor(Sensor):
    """ this class gives access to power contactors """
    registers = Sensor.registers + ['status']

    def __init__(self, name, devices):
        """
            devices must be formated such as:
            devices = {
                'name1': [pin_number, normal_mode],
                'name2': [pin_number, normal_mode],
                ...
                # where normal_mode must be in ('normal_open', 'normal_close')
            }
        """
        Sensor.__init__(self, name)

        self._devices = devices
        self._status = {}

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for name, (pin, normal) in self._devices.items():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            self._status[name] = 'disable' if normal == 'normal_open' else 'enable'

    @property
    def status(self):
        return self._status

    def enable(self, device):
        pin, normal = self._devices[device]
        GPIO.output(pin, GPIO.HIGH if normal == 'normal_close' else GPIO.LOW)
        self._status[device] = 'enable'

    def disable(self, device):
        pin, normal = self._devices[device]
        GPIO.output(pin, GPIO.LOW if normal == 'normal_close' else GPIO.HIGH)
        self._status[device] = 'disable'


import time

import RPi.GPIO as GPIO

from ...robot.sensor import Sensor


class PowerContactor(Sensor):
    """this class give access to power contactor"""
    registers = Sensor.registers + ['status_list']

    def __init__(self, name, device_list):
        Sensor.__init__(self, name)
        self.normal = {'normalOpen': 0,
                       'normalClose': 1}
        # devicelist is formated like
        # 'device name': [pinNumber, normal ('normalOpen' or 'normalClose')]
        self._device_list = device_list
        self._status_list = {}
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for item in self._device_list:
            GPIO.setup(self._device_list[item][0], GPIO.OUT)
            GPIO.output(self._device_list[item][0], GPIO.HIGH)
            if self._device_list[item][1] == 'normalOpen':
                self._status_list[item] = 'disable'
            else:
                self._status_list[item] = 'enable'

    @property
    def status_list(self):
        return self._status_list

    def enable(self, device):
        if self._device_list[device][1] == 'normalClose':
            GPIO.output(self._device_list[device][0],
                        GPIO.HIGH)
        else:
            GPIO.output(self._device_list[device][0],
                        GPIO.LOW)
        self._status_list[device] = 'enable'

    def disable(self, device):
        if self._device_list[device][1] == 'normalClose':
            GPIO.output(self._device_list[device][0],
                        GPIO.LOW)
        else:
            GPIO.output(self._device_list[device][0],
                        GPIO.HIGH)
        self._status_list[device] = 'disable'

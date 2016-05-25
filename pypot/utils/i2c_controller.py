import smbus
import threading


class I2cController(object):
    used_bus = {}

    def __init__(self, pin_number):
        if pin_number not in I2cController.used_bus:
            I2cController.used_bus[pin_number] = smbus.SMBus(pin_number)

        self.bus = I2cController.used_bus[pin_number]
        self.lock = threading.Lock()

    def read_byte_data(self, addr, cmd):
        with self.lock:
            return self.bus.read_byte_data(addr, cmd)

    def write_byte_data(self, addr, cmd, val):
        with self.lock:
            return self.bus.write_byte_data(addr, cmd, val)

    def read_word_data(self, addr, cmd):
        with self.lock:
            return self.bus.read_word_data(addr, cmd)

    def write_word_data(self, addr, cmd, val):
        with self.lock:
            return self.bus.write_word_data(addr, cmd, val)

import time
import smbus
import threading


def get_value_or_die_trying(func):
    def wrapped_func(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except IOError:
                time.sleep(0.005)

    return wrapped_func


class I2cController(object):
    used_bus = {}

    def __init__(self, pin_number):
        if pin_number not in I2cController.used_bus:
            I2cController.used_bus[pin_number] = smbus.SMBus(pin_number)

        self.bus = I2cController.used_bus[pin_number]
        self.lock = threading.Lock()

    @get_value_or_die_trying
    def read_byte_data(self, addr, cmd):
        with self.lock:
            return self.bus.read_byte_data(addr, cmd)

    @get_value_or_die_trying
    def write_byte_data(self, addr, cmd, val):
        with self.lock:
            return self.bus.write_byte_data(addr, cmd, val)

    @get_value_or_die_trying
    def read_word_data(self, addr, cmd):
        with self.lock:
            return self.bus.read_word_data(addr, cmd)

    @get_value_or_die_trying
    def write_word_data(self, addr, cmd, val):
        with self.lock:
            return self.bus.write_word_data(addr, cmd, val)

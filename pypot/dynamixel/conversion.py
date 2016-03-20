# -*- coding: utf-8 -*-


"""
    This module describes all the conversion method used to transform value from the representation used by the dynamixel motor to a more standard form (e.g. degrees, volt...).

    For compatibility issue all comparison method should be written in the following form (even if the model is not actually used):
        * def my_conversion_from_dxl_to_si(value, model): ...
        * def my_conversion_from_si_to_dxl(value, model): ...

    .. note:: If the control is readonly you only need to write the dxl_to_si conversion.

    """

import numpy
import itertools

from enum import Enum

# MARK: - Position

position_range = {
    'MX': (4096, 360.0),
    '*': (1024, 300.0)
}

torque_max = {  # in N.m
    'MX-106': 8.4,
    'MX-64': 6.,
    'MX-28': 2.5,
    'MX-12': 1.2,
    'AX-12': 1.2,
    'AX-18': 1.8,
    'RX-24': 2.6,
    'RX-28': 2.5,
    'RX-64': 4.,
    'XL-320': 0.39,
}

velocity = {  # in degree/s
    'MX-106': 270.,
    'MX-64': 378.,
    'MX-28': 330.,
    'MX-12': 2820.,
    'AX-12': 354.,
    'AX-18': 582.,
    'RX-24': 756.,
    'RX-28': 402.,
    'RX-64': 294.,
}


def dxl_to_degree(value, model):
    model = 'MX' if model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]

    return round(((max_deg * float(value)) / (max_pos - 1)) - (max_deg / 2), 2)


def degree_to_dxl(value, model):
    model = 'MX' if model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]

    pos = int(round((max_pos - 1) * ((max_deg / 2 + float(value)) / max_deg), 0))
    pos = min(max(pos, 0), max_pos - 1)

    return pos

# MARK: - Speed


def dxl_to_speed(value, model):
    cw, speed = divmod(value, 1024)
    direction = (-2 * cw + 1)

    speed_factor = 0.114 if model.startswith('MX') else 0.111

    return direction * (speed * speed_factor) * 6


def speed_to_dxl(value, model):
    direction = 1024 if value < 0 else 0
    speed_factor = 0.114 if model.startswith('MX') else 0.111

    max_value = 1023 * speed_factor * 6
    value = min(max(value, -max_value), max_value)

    return int(round(direction + abs(value) / (6 * speed_factor), 0))

# MARK: - Torque


def dxl_to_torque(value, model):
    return round(value / 10.23, 1)


def torque_to_dxl(value, model):
    return int(round(value * 10.23, 0))


def dxl_to_load(value, model):
    cw, load = divmod(value, 1024)
    direction = -2 * cw + 1

    return dxl_to_torque(load, model) * direction

# PID Gains


def dxl_to_pid(value, model):
    return (value[0] * 0.004,
            value[1] * 0.48828125,
            value[2] * 0.125)


def pid_to_dxl(value, model):
    truncate = lambda x: int(max(0, min(x, 254)))
    return [truncate(x * y) for x, y in zip(value, (250, 2.048, 8.0))]

# MARK: - Model

dynamixelModels = {
    12: 'AX-12',    # 12 + (0<<8)
    18: 'AX-18',    # 18 + (0<<8)
    24: 'RX-24',    # 24 + (0<<8)
    28: 'RX-28',    # 28 + (0<<8)
    29: 'MX-28',    # 29 + (0<<8)
    64: 'RX-64',    # 64 + (0<<8)
    360: 'MX-12',   # 104 + (1<<8)
    310: 'MX-64',   # 54 + (1<<8)
    320: 'MX-106',  # 64 + (1<<8)
    350: 'XL-320',  # 94 + (1<<8)
}


def dxl_to_model(value, dummy=None):
    return dynamixelModels[value]
# MARK: - Drive Mode


def check_bit(value, offset):
    return bool(value & (1 << offset))


def dxl_to_drive_mode(value, model):
    return ('reverse' if check_bit(value, 0) else 'normal',
            'slave' if check_bit(value, 1) else 'master')


def drive_mode_to_dxl(value, model):
    return (int('slave' in value) << 1 | int('reverse' in value))

# MARK: - Baudrate

dynamixelBaudrates = {
    1: 1000000.0,
    3: 500000.0,
    4: 400000.0,
    7: 250000.0,
    9: 200000.0,
    16: 117647.1,
    34: 57600.0,
    103: 19230.8,
    207: 9615.4,
    250: 2250000.0,
    251: 2500000.0,
    252: 3000000.0,
}


def dxl_to_baudrate(value, model):
    return dynamixelBaudrates[value]


def baudrate_to_dxl(value, model):
    for k, v in dynamixelBaudrates.iteritems():
        if (abs(v - value) / float(value)) < 0.05:
            return k
    raise ValueError('incorrect baudrate {} (possible values {})'.format(value, dynamixelBaudrates.values()))

# MARK: - Return Delay Time


def dxl_to_rdt(value, model):
    return value * 2


def rdt_to_dxl(value, model):
    return int(value / 2)

# MARK: - Temperature


def dxl_to_temperature(value, model):
    return float(value)


def temperature_to_dxl(value, model):
    return int(value)

# MARK: - Voltage


def dxl_to_voltage(value, model):
    return value * 0.1


def voltage_to_dxl(value, model):
    return int(value * 10)

# MARK: - Status Return Level

status_level = ('never', 'read', 'always')


def dxl_to_status(value, model):
    return status_level[value]


def status_to_dxl(value, model):
    if value not in status_level:
        raise ValueError('status "{}" should be chosen among {}'.format(value, status_level))
    return status_level.index(value)

# MARK: - Error

# TODO: depend on protocol v1 vs v2
dynamixelErrors = ['None Error',
                   'Instruction Error',
                   'Overload Error',
                   'Checksum Error',
                   'Range Error',
                   'Overheating Error',
                   'Angle Limit Error',
                   'Input Voltage Error']


def dxl_to_alarm(value, model):
    return decode_error(value)


def decode_error(error_code):
    bits = numpy.unpackbits(numpy.asarray(error_code, dtype=numpy.uint8))
    return tuple(numpy.array(dynamixelErrors)[bits == 1])


def alarm_to_dxl(value, model):
    if not set(value).issubset(dynamixelErrors):
        raise ValueError('should only contains error among {}'.format(dynamixelErrors))

    indices = [len(dynamixelErrors) - 1 - dynamixelErrors.index(e) for e in value]
    return sum(2 ** i for i in indices)


XL320LEDColors = Enum('Colors', 'off red green yellow '
                      'blue pink cyan white')


def dxl_to_led_color(value, model):
    return XL320LEDColors(value + 1).name


def led_color_to_dxl(value, model):
    value = getattr(XL320LEDColors, value).value - 1
    value = int(value) & 0b111
    return value

control_modes = {
    1: 'wheel',
    2: 'joint',
}

dxl_to_control_mode = lambda value, _: control_modes[value]
control_mode_to_dxl = lambda mode, _: (next((v for v, m in control_modes.items()
                                             if m == mode), None))

# MARK: - Various utility functions


def dxl_to_bool(value, model):
    return bool(value)


def bool_to_dxl(value, model):
    return int(value)


def dxl_decode(data):
    if len(data) not in (1, 2):
        raise ValueError('try to decode incorrect data {}'.format(data))

    if len(data) == 1:
        return data[0]

    if len(data) == 2:
        return data[0] + (data[1] << 8)


def dxl_decode_all(data, nb_elem):
    if nb_elem > 1:
        data = list(itertools.izip(*([iter(data)] * (len(data) // nb_elem))))
        return tuple(map(dxl_decode, data))
    else:
        return dxl_decode(data)


def dxl_code(value, length):
    if length not in (1, 2):
        raise ValueError('try to code value with an incorrect length {}'.format(length))

    if length == 1:
        return (value, )

    if length == 2:
        return (value % 256, value >> 8)


def dxl_code_all(value, length, nb_elem):
    if nb_elem > 1:
        return list(itertools.chain(*(dxl_code(v, length) for v in value)))
    else:
        return dxl_code(value, length)

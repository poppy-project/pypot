# -*- coding: utf-8 -*-


"""
    This module describes all the conversion method used to transform value from the representation used by the herkulex motor to a more standard form (e.g. degrees, volt...).

    For compatibility issue all comparison method should be written in the following form (even if the model is not actually used):
        * def my_conversion_from_hkx_to_si(value, model): ...
        * def my_conversion_from_si_to_hkx(value, model): ...

    .. note:: If the control is readonly you only need to write the hkx_to_si conversion.

    """

import numpy
import itertools

from enum import Enum

hkx_max_playtime = 2.856  #the maximum playtime for JOG commands (in secs)
hkx_max_speed = 360    #the maximum speed in deg/sec

# MARK: - Model

herkulexModels = {
    257: 'DRS-0101',
    513: 'DRS-0201',
    1025: 'DRS-0401',
    1026: 'DRS-0402',
    1537: 'DRS-0601',
    1538: 'DRS-0602',
}

def hkx_to_model(value, dummy=None):
    return herkulexModels[value]


# MARK: - Position

position_range = {
    'DRS-0101': (1024, 333.3)
}

def hkx_to_degree(value, model):
    max_pos, max_deg = position_range[model]
    return round(((max_deg * float(value)) / (max_pos - 1)) - (max_deg / 2), 2)


def degree_to_hkx(value, model):
    max_pos, max_deg = position_range[model]
    pos = int(round((max_pos - 1) * ((max_deg / 2 + float(value)) / max_deg), 0))
    pos = min(max(pos, 0), max_pos - 1)
    return pos


# MARK: - Speed

def hkx_to_speed(value, model):
    return value

def speed_to_hkx(value, model):
    return value


# MARK: - Torque value
#TODO
def hkx_to_torque(value, model):
    return value


def torque_to_hkx(value, model):
    return value


def hkx_to_load(value, model):
    return value


# MARK: - Torque mode

torque_control_modes = {
    'BREAK_ON' : 0x40,
    'TORQUE_ON' : 0x60,
    'TORQUE_FREE' : 0x00,
}

def hkx_to_torque_enabled(value, model):
    return value == torque_control_modes['TORQUE_ON']

def torque_enabled_to_hkx(value, model):
    res = torque_control_modes['TORQUE_ON']
    if not value:
        res = torque_control_modes['TORQUE_FREE']
    return res
    
    
# MARK: - Control mode

def hkx_to_control_mode(value, model):
    if value == 0:
        res = 'joint'        
    elif value == 1:
        res = 'wheel'
    return res

def control_mode_to_hkx(value, model):
    if value == 'wheel':
        res = 0       
    elif value == 'joint':
        res = 1
    return res


# MARK: - Status data

status_detail_bits = {
    0: "Moving",
    1: "In_position",
    2: "Invalid packet: checksum error",
    3: "Invalid packet: unknown command",
    4: "Invalid packet: exceed REG range",
    5: "Invalid packet: garbage detected",
    6: "MOTOR_ON",
    7: "reserved",
    }

def hkx_to_status_detail(value, model):
    return [status_detail_bits[a] for a in status_detail_bits if check_bit(value, int(a))]


# MARK: - Baudrate

herculexBaudrates = {
    0x02: 666666.0,
    0x03: 500000.0,
    0x04: 400000.0,
    0x07: 250000.0,
    0x09: 200000.0,
    0x10: 115200.0,
    0x22: 57600.0,
}

def hkx_to_baudrate(value, model):
    return herculexBaudrates[value]


def baudrate_to_hkx(value, model):
    for k, v in herculexlBaudrates.iteritems():
        if (abs(v - value) / float(value)) < 0.05:
            return k
    raise ValueError('incorrect baudrate {} (possible values {})'.format(value, herculex.values()))


# MARK: - Temperature
##TODO: add tabulated values
def hkx_to_temperature(value, model):
    return int(value)


def temperature_to_hkx(value, model):
    return int(value)


# MARK: - time (ticks vs s)

def hkx_to_time(value, model):
    return float(value * 0.0112)


def time_to_hkx(value, model):
    res = int(value / 0.0112)
    return res

# MARK: - Voltage

voltage_factor = {
    'DRS-0101': 0.074075,
    'DRS-0602': 0.1,
}

def hkx_to_voltage(value, model):
    return value * voltage_factor[model]


def voltage_to_hkx(value, model):
    return int(value / voltage_factor[model])


# MARK: - led color

LEDColors = Enum('Colors', 'off green blue cyan red yellow pink white')

def hkx_to_LED(value, model):
    return LEDColors(value + 1).name


def LED_to_hkx(value, model):
    value = getattr(LEDColors, value).value - 1
    value = int(value) & 0b111
    return value


# MARK: - acceleration ratio

def accel_ratio_to_hkx(value, model):
    if value < 0 or value > 0.5:
        raise ValueError('acceleration ratio must be between 0 and 50%')
    res = int(value * 100)
    return res

# MARK: - Error

herkulexErrors = [ 'reserved',
                   'EEP REG distorted Error',
                   'Driver fault Error',
                   'Overload Error',
                   'Invalid packet Error',
                   'Overheating Error',
                   'Angle Limit Error',
                   'Input Voltage Error']

def hkx_to_status_error(value, model):
    return decode_error(value)

    
def decode_error(error_code):
    bits = numpy.unpackbits(numpy.asarray(error_code, dtype=numpy.uint8))
    return tuple(numpy.array(herkulexErrors)[bits == 1])


# MARK: - Various utility functions

def check_bit(value, offset):
    return bool(value & (1 << offset))
    
def hkx_decode(data):
    if len(data) not in (1, 2):
        raise ValueError('try to decode incorrect data {}'.format(data))

    if len(data) == 1:
        return data[0]

    if len(data) == 2:
        return data[0] + (data[1] << 8)


def hkx_decode_all(data, nb_elem):
    if nb_elem > 1:
        data = list(itertools.izip(*([iter(data)] * (len(data) // nb_elem))))
        return tuple(map(hkx_decode, data))
    else:
        return hkx_decode(data)


def hkx_code(value, length):
    if length not in (1, 2):
        raise ValueError('try to code value with an incorrect length {}'.format(length))

    if length == 1:
        return (value, )

    if length == 2:
        return (value % 256, value >> 8)


def hkx_code_all(value, length, nb_elem):
    if nb_elem > 1:
        return list(itertools.chain(*(hkx_code(v, length) for v in value)))
    else:
        return hkx_code(value, length)

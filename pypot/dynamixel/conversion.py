# -*- coding: utf-8 -*-


"""
    This module describes all the conversion method used to transform value
    from the representation used by the dynamixel motor to a more standard form.
    
    For compatibility issue all comparison method should be written in the
    following form (even if the model is not actually used):
        * def my_conversion_from_dxl_to_si(value, model): ...
        * def my_conversion_from_si_to_dxl(value, model): ...
    
    .. note:: If the control is readonly you only need to write the dxl_to_si conversion.
    
    """

import numpy
import numbers


# MARK: - Position 

position_range = {
    'MX': (4096, 360.0),
    '*': (1024, 300.0)
}

def dxl_to_degree(value, model):
    model = 'MX' if model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]

    check_range(value, 0, max_pos)

    return round(((max_deg * float(value)) / (max_pos - 1)) - (max_deg / 2), 2)

def degree_to_dxl(value, model):
    model = 'MX' if model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]

    check_range(value, -max_deg / 2, max_deg / 2)

    return int(round((max_pos - 1) * ((max_deg / 2 + float(value)) / max_deg), 0))

# MARK: - Speed

def dxl_to_oriented_speed(value, model):
    cw, speed = divmod(value, 1024)
    direction = 2 * cw - 1
    
    return dxl_to_speed(speed, model) * direction

def dxl_to_speed(value, model):
    check_range(value, 0, 1023)
    return (value * 0.114) * 6

def speed_to_dxl(value, model):
    check_range(value, 0, 700)
    return int(value / (6 * 0.114))

# MARK: - Torque

def dxl_to_torque(value, model):
    check_range(value, 0, 1023)
    return round(value / 10.23, 1)

def torque_to_dxl(value, model):
    check_range(value, 0, 100)
    return int(round(value * 10.23, 0))

def dxl_to_oriented_load(value, model):
    cw, load = divmod(value, 1024)
    direction = 2 * cw - 1
    
    return dxl_to_torque(load, model) * direction


# MARK: - Model 

dynamixelModels = {
    12: 'AX-12',
    28: 'RX-28',
    64: 'RX-64',
    29: 'MX-28'
}

def dxl_to_model(value, _):
    return dynamixelModels[value]

# MARK: - Baudrate 

dynamixelBaudrates = {
    1: 1000000.0,
    3: 500000.0,
    4: 400000.0,
    7: 250000.0,
    9: 200000.0,
    16: 117647.1,
    34: 57142.9,
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
        if v == value:
            return k
    raise ValueError('incorrect baudrate {} (possible values {})'.format(value, dynamixelBaudrates.values()))

# MARK: - Return Delay Time

def dxl_to_rdt(value, model):
    return value * 2

def rdt_to_dxl(value, model):
    return int(value / 2)

# MARK: - Temperature

def dxl_to_temperature(value, model):
    check_range(value, 10, 99)
    return value

temperature_to_dxl = dxl_to_temperature

# MARK: - Voltage

def dxl_to_voltage(value, model):
    check_range(value, 50, 250)
    return value * 0.1

def voltage_to_dxl(value, model):
    check_range(value, 5, 25)
    return int(value * 10)

# MARK: - Status Return Level

status_level = ('never', 'read', 'always')

def dxl_to_status(value, model):
    check_range(value, 0, len(status_level) - 1)
    return status_level[value]

def status_to_dxl(value, model):
    if value not in status_level:
        raise ValueError('status "{}" should be chosen among {}'.format(value, status_level))
    return status_level.index(value)

# MARK: - Error

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
    check_range(error_code, 0, 255)
    
    bits = numpy.unpackbits(numpy.asarray(error_code, dtype=numpy.uint8))
    return tuple(numpy.array(dynamixelErrors)[bits == 1])

def alarm_to_dxl(value, model):
    if not set(value).issubset(dynamixelErrors):
        raise ValueError('should only contains error among {}'.format(dynamixelErrors))
    
    indices = [len(dynamixelErrors) - 1 - dynamixelErrors.index(e) for e in value]
    return sum(2 ** i for i in indices)


# MARK: - Various utility functions

def check_range(val, min, max):
    if not (isinstance(val, numbers.Number) and min <= val <= max):
        raise ValueError('{} not in range [{}, {}]'.format(val, min, max))

def dxl_to_bool(value, model):
    check_range(value, 0, 1)
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
    
    
def dxl_code(value, length):
    if length not in (1, 2):
        raise ValueError('try to code value with an incorrect length {}'.format(length))

    if length == 1:
        return (value, )

    if length == 2:
        return (value % 256, value >> 8)

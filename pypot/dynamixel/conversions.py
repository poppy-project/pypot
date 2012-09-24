import math
import numpy

from pypot.dynamixel.protocol import DXL_ALARMS


# for details, see http://support.robotis.com/en/product/dynamixel/

# MARK : Unit conversions

position_range = {
    'MX' : (4096, 360.0),
    '*' : (1024, 300.0)
}

def position_to_degree(position, motor_model):
    model = 'MX' if motor_model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]
    
    if not (0 <= position < max_pos):
        raise ValueError('Position must be in [0, %d[' % (max_pos))
    
    return round(((max_deg * float(position)) / (max_pos - 1)) - (max_deg / 2), 2)


def degree_to_position(degree, motor_model):
    model = 'MX' if motor_model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]
    
    max_deg /= 2
    
    if not (-max_deg <= degree <= max_deg):
        raise ValueError('Degree must be in [%f, %f]' % (-max_deg, max_deg))
    
    return int(round((max_pos - 1) * ((max_deg + float(degree)) / (max_deg * 2)), 0))


SPEED_TO_RPM = 0.114
SPEED_MAX = 2048
RPM_MAX = ((SPEED_MAX / 2) - 1) * SPEED_TO_RPM

def speed_to_rpm(speed):
    if not (0 <= speed < SPEED_MAX):
        raise ValueError('Speed must be in [0, %d[' % (SPEED_MAX))
    
    direction = 2 * (speed >> 10) - 1
    speed = speed % (SPEED_MAX / 2)
        
    return round(direction * speed * SPEED_TO_RPM, 2)


def rpm_to_speed(rpm):
    if not (-RPM_MAX <= rpm <= RPM_MAX):
        raise ValueError('Rpm must be in [%d, %d]' % (int(-RPM_MAX), int(RPM_MAX)))
    
    speed = abs(rpm) / SPEED_TO_RPM
    
    if rpm > 0:
        speed += SPEED_MAX / 2
    
    return int(round(speed, 0))

def speed_to_dps(speed):
    return speed_to_rpm(speed) * 6

def dps_to_speed(dps):
    return rpm_to_speed(dps / 6.0)


LOAD_MAX = 2048
LOAD_TO_PERCENT = 100.0 / ((LOAD_MAX / 2) - 1)

def load_to_percent(load):
    """
        Maps the load values according to
        http://support.robotis.com/en/product/dynamixel/mx_series/mx-28.htm#Actuator_Address_28
        
        """
    if not (0 <= load < LOAD_MAX):
        raise ValueError('Load must be in [0, %d[' % (LOAD_MAX))
    
    direction = 2 * (int(load) >> 10) - 1
    load = load % (LOAD_MAX / 2)
    
    return round(direction * load * LOAD_TO_PERCENT, 2)


MAX_TORQUE = 1023

def torque_limit_to_percent(torque):
    if not (0 <= torque <= MAX_TORQUE):
        raise ValueError('Torque must be in [0, %d]' % (MAX_TORQUE))
    return round((torque / float(MAX_TORQUE)) * 100, 1)

def percent_to_torque_limit(percent):
    if not (0 <= percent <= 100):
        raise ValueError('Percent must be in [0, 100]')
    
    return int(round(percent * (MAX_TORQUE / 100.0), 0))

# MARK: - Alarm conversions

def byte_to_alarms(alarm_code):
    if not (0 <= alarm_code <= 255):
        raise ValueError('alarm code must be in [0, 255]')
    
    byte = numpy.unpackbits(numpy.asarray(alarm_code, dtype=numpy.uint8))
    return tuple(numpy.array(DXL_ALARMS)[byte == 1])

def alarms_to_byte(alarms):
    b = 0
    for a in alarms:
        b += 2 ** (7 - DXL_ALARMS.index(a))
    return b


# MARK: - Byte conversions

def integer_to_two_bytes(value):
    return (int(value % 256), int(value >> 8))

def two_bytes_to_integer(value):
    return int(value[0] + (value[1] << 8))



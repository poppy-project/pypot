import math

# for details, see http://support.robotis.com/en/product/dynamixel/

# MARK : Unit conversions

position_range = {
    'MX' : (4096, 360.0),
    '*' : (1024, 300.0)
}

def position_to_degree(position, motor_model):
    model = 'MX' if motor_model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]
    
    if not (0 <= position <= max_pos):
        raise ValueError('Position must be in [0, %d]' % (max_pos))
    
    return (float(position) / max_pos) * max_deg


def degree_to_position(degree, motor_model):
    model = 'MX' if motor_model.startswith('MX') else '*'
    max_pos, max_deg = position_range[model]
    
    if not (0 <= degree <= max_deg):
        raise ValueError('Degree must be in [0, %f]' % (max_deg))
    
    return int((degree / max_deg) * max_pos)

SPEED_TO_RPM = 0.114
SPEED_MAX = 2047
SPEED_MID = 1024
RPM_MAX = 117.0

def speed_to_rpm(speed):
    if not (0 <= speed <= SPEED_MAX):
        raise ValueError('Speed must be in [0, %d]' % (SPEED_MAX))
    
    
    direction = ((speed >> 10) * 2) - 1
    
    rpm = (speed % SPEED_MID) * SPEED_TO_RPM
    
    return float(direction * rpm)


def rpm_to_speed(rpm):
    if not (-RPM_MAX <= rpm <= RPM_MAX):
        raise ValueError('Rpm must be in [%d, %d]' % (int(-RPM_MAX), int(RPM_MAX)))
    
    speed = (SPEED_MID - 1) * (abs(rpm) / RPM_MAX)
    
    if rpm > 0:
        speed += SPEED_MID
    
    return int(round(speed, 0))

LOAD_MAX = 2047
LOAD_MID = 1024

def load_to_percent(load):
    """
        Maps the load values according to
        http://support.robotis.com/en/product/dynamixel/mx_series/mx-28.htm#Actuator_Address_28
        
        """
    if not (0 <= load <= LOAD_MAX):
        raise ValueError('Load must be in [0, %d]' % (LOAD_MAX))
    
    direction = ((load >> 10) * 2) - 1
    
    percent = (load % LOAD_MID) * 0.1
    percent = max(min(percent, 100.0), 0.0)
    
    return direction * percent

MAX_TORQUE = 1023

def percent_to_torque_limit(percent):
    if not (0 <= percent <= 100):
        raise ValueError('Percent must be in [0, 100]')
    
    return int(percent * (MAX_TORQUE / 100.0))


# MARK: - Byte conversions

def integer_to_two_bytes(value):
    return (int(value % 256), int(value >> 8))

def two_bytes_to_integer(value):
    return int(value[0] + (value[1] << 8))



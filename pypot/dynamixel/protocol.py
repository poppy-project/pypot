# For details on the dynamixel protocol you should refer to
# http://support.robotis.com/en/product/dxl_main.htm

DXL_INSTRUCTIONS = {
    'PING': 0x01,
    'READ_DATA': 0x02,
    'WRITE_DATA': 0x03,
    'SYNC_WRITE': 0x83,
    'SYNC_READ': 0x84,
}

DXL_BROADCAST = 0xFE

DXL_CONTROLS = {
    # control_name : (address, number_of_data, data_length)
    
    # EEPROM
    'MODEL_NUMBER': (0x00, 1, 2),
    'VERSION': (0x02, 1, 1),
    'ID': (0x03, 1, 1),
    'BAUD_RATE': (0x04, 1, 1),
    'RETURN_DELAY_TIME': (0x05, 1, 1),
    'CW_ANGLE_LIMIT': (0x06, 1, 2),
    'CCW_ANGLE_LIMIT': (0x08, 1, 2),
    'ANGLE_LIMITS': (0x06, 2, 2),
    'DRIVE_MODE': (0x0A, 1, 1), # EX only
    'HIGHEST_LIMIT_TEMPERATURE': (0x0B, 1, 1),
    'LOWEST_LIMIT_VOLTAGE': (0x0C, 1, 1),
    'HIGHEST_LIMIT_VOLTAGE': (0x0D, 1, 1),
    'VOLTAGE_LIMITS': (0x0C, 2, 1),
    'MAX_TORQUE': (0x0E, 1, 2),
    'STATUS_RETURN_LEVEL': (0x10, 1, 1),
    'ALARM_LED': (0x11, 1, 1),
    'ALARM_SHUTDOWN': (0x12, 1, 1),
	
    # RAM
    'TORQUE_ENABLE': (0x18, 1, 1),
    'LED': (0x19, 1, 1),
    
    # MX series
    'D_GAIN': (0x1A, 1, 1),
    'I_GAIN': (0x1B, 1, 1),
    'P_GAIN': (0x1C, 1, 1),
    'GAINS': (0x1A, 3, 1),
    # AX RX series
    'CW_COMPLIANCE_MARGIN': (0x1A, 1, 1),
    'CCW_COMPLIANCE_MARGIN': (0x1B, 1, 1),
    'COMPLIANCE_MARGINS': (0x1A, 2, 1),
    'CW_COMPLIANCE_SLOPE': (0x1C, 1, 1),
    'CCW_COMPLIANCE_SLOPE': (0x1D, 1, 1),
    'COMPLIANCE_SLOPES': (0x1C, 2, 1),
    
    'GOAL_POSITION': (0x1E, 1, 2),
    'MOVING_SPEED': (0x20, 1, 2),
    'TORQUE_LIMIT': (0x22, 1, 2),
    'GOAL_POS_SPEED_TORQUE': (0x1E, 3, 2),
    
    'PRESENT_POSITION': (0x24, 1, 2),
    'PRESENT_POS_SPEED_LOAD': (0x24, 3, 2),
    'PRESENT_SPEED': (0x26, 1, 2),
    'PRESENT_LOAD': (0x28, 1, 2),
    'PRESENT_VOLTAGE': (0x2A, 1, 1),
    'PRESENT_TEMPERATURE': (0x2B, 1, 1),
    'REGISTERED': (0x2C, 1, 1),
    'MOVING': (0x2E, 1, 1),
    'LOCK': (0x2F, 1, 1),
    'PUNCH': (0x30, 1, 2),
    
    'SENSED_CURRENT': (0x38, 1, 2), # EX only
    'CURRENT': (0x44, 1, 2), # MX64 and MX106
}

DXL_MODEL_NUMBER = {
    12: 'AX-12',
    18: 'AX-18',
    44: 'AX-12W',
	
    10: 'RX-10',
    24: 'RX-24F',
    28: 'RX-28',
    64: 'RX-64',
	
    29: 'MX-28',
    54: 'MX-64',
    64: 'MX-106',
}

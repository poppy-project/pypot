import xml.dom.minidom
import logging
import time

import pypot.robot
import pypot.dynamixel


def from_configuration(filename):
    dom = xml.dom.minidom.parse(filename)
    return parse_robot_node(dom.firstChild)

def parse_robot_node(robot_node):
    robot = pypot.robot.Robot()
    
    controllers_node = robot_node.getElementsByTagName('DxlController')
    for c in controllers_node:
        dxl_io, dxl_motors = parse_controller_node(c)
        robot._attach_dxl_motors(dxl_io, dxl_motors)

    motors_group_node = robot_node.getElementsByTagName('DxlMotorGroup')
    for g in motors_group_node:
        group_name, motor_names = parse_motor_group_node(g)
        motors = [getattr(robot, name) for name in motor_names]
        setattr(robot, group_name, motors)

    return robot

def parse_motor_group_node(motor_group_node):
    name = motor_group_node.getAttribute('name')

    motors_node = motor_group_node.getElementsByTagName('DxlMotor')
    motors_name = [m.getAttribute('name') for m in motors_node]

    return name, motors_name

def parse_controller_node(controller_node):
    sync_read = bool(controller_node.getAttribute('sync_read'))
    port = controller_node.getAttribute('port')
    
    dxl_io = pypot.dynamixel.DxlIO(port, use_sync_read=sync_read, error_handler_cls=pypot.dynamixel.BaseErrorHandler)

    changed_angle_limits = {}
    
    motors_node = controller_node.getElementsByTagName('DxlMotor')
    dxl_motors = []
    for motor_node in motors_node:
        m, angle_limit = parse_motor_node(motor_node)
        old_limits = dxl_io.get_angle_limit(m.id)[0] # Suppose qu'il n'y a pas de timeout

        d = abs(sum(map(lambda l1, l2: l1 - l2, old_limits, angle_limit)))
        if d > 1:
            logging.warning('changes angle limit of motor {} to {}'.format(m.id, angle_limit))
            changed_angle_limits[m.id] = angle_limit
        
        dxl_motors.append(m)
    
    if changed_angle_limits:
        dxl_io.set_angle_limit(changed_angle_limits)
        time.sleep(1)
    
    return (dxl_io, dxl_motors)

def parse_motor_node(motor_node):
    name = str(motor_node.getAttribute('name'))
    id = int(motor_node.getAttribute('id'))
    direct = True if motor_node.getAttribute('orientation') == 'direct' else False
    offset = float(motor_node.getAttribute('offset'))
    motor = pypot.dynamixel.DxlMotor(id, name, direct, offset)

    angle_limit_node = motor_node.getElementsByTagName('angle_limits')[0]
    angle_limit = eval(angle_limit_node.firstChild.data)
    
    return (motor, angle_limit)


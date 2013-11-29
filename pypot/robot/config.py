import itertools
import logging
import numpy
import time

import pypot.robot
import pypot.dynamixel

from pypot.dynamixel.motor import DxlAXRXMotor, DxlMXMotor

ergo_robot_config = {
    'controllers': {
        'my_dxl_controller': {
            'port': '/dev/ttyUSB0', # Depends on your OS
            'sync_read': False,
            'attached_motors': ['base', 'head'], # You can mix motorgroups or individual motors
        },
    },

    'motorgroups': {
        'base': ['base_pan', 'base_tilt_lower', 'base_tilt_upper'],
        'head': ['head_pan', 'head_tilt_lower', 'head_tilt_upper'],
    },

    'motors': {
        'base_pan': {
            'id': 11,
            'type': 'RX-64',
            'orientation': 'direct',
            'offset': 22.5,
            'angle_limit': (-67.5, 112.5),
        },
        'base_tilt_lower': {
            'id': 12,
            'type': 'RX-64',
            'orientation': 'direct',
            'offset': 0.0,
            'angle_limit': (-90.0, 90.0),
        },
        'base_tilt_upper': {
            'id': 13,
            'type': 'RX-64',
            'orientation': 'direct',
            'offset': 0.0,
            'angle_limit': (-90.0, 90.0),
        },
        'head_pan': {
            'id': 14,
            'type': 'RX-28',
            'orientation': 'direct',
            'offset': 22.5,
            'angle_limit': (-67.5, 112.5),
        },
        'head_tilt_lower': {
            'id': 15,
            'type': 'RX-28',
            'orientation': 'indirect',
            'offset': 0.0,
            'angle_limit': (-90.0, 90.0),
        },
        'head_tilt_upper': {
            'id': 16,
            'type': 'RX-28',
            'orientation': 'indirect',
            'offset': 0.0,
            'angle_limit': (-90.0, 90.0),
        },
    },
}



def from_config(config):
    """ Returns a Robot instance created from a configuration dictionnary.

        For details on how to write such a configuration dictionnary, you should refer to the section TODO:BLABLABLA.

        """
    robot = pypot.robot.Robot()

    # Instatiate the different controllers
    for c_name, c_params in config['controllers'].items():
        dxl_io = pypot.dynamixel.DxlIO(port=c_params['port'],
                                       use_sync_read=c_params['sync_read'],
                                       error_handler_cls=pypot.dynamixel.BaseErrorHandler)

        dxl_motors = []
        motor_names = _extract_motors_fullist(config, c_params['attached_motors'])
        motor_nodes = map(lambda m: (m, config['motors'][m]), motor_names)
        changed_angle_limits = {}

        # Instatiate the attached motors and set their angle_limits if needed
        for m_name, m_params in motor_nodes:
            MotorCls = DxlMXMotor if m_params['type'].startswith('MX') else DxlAXRXMotor

            m = MotorCls(id=m_params['id'],
                         name=m_name,
                         direct=True if m_params['orientation'] == 'direct' else False,
                         offset=m_params['offset'])

            dxl_motors.append(m)

            angle_limit = m_params['angle_limit']

            old_limits = dxl_io.get_angle_limit((m.id, ))[0]
            d = numpy.linalg.norm(numpy.asarray(angle_limit) - numpy.asarray(old_limits))

            if d > 1:
                logging.warning('changes angle limit of motor {} to {}'.format(m.id, angle_limit))
                changed_angle_limits[m.id] = angle_limit

        if changed_angle_limits:
            dxl_io.set_angle_limit(changed_angle_limits)
            time.sleep(1)

        robot._attach_dxl_motors(dxl_io, dxl_motors)

    # Create the alias for the motorgroups
    for alias, motor_names in config['motorgroups'].items():
        motors = [getattr(robot, name) for name in motor_names]
        setattr(robot, alias, motors)
        robot.alias.append(alias)

    return robot

def _extract_motors_fullist(config, attached_motors):
    groups = config['motorgroups']

    motors = [groups[name] if name in groups else [name] for name in attached_motors]
    return list(itertools.chain(*motors))
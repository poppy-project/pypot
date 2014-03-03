"""
The config module allows the definition of the structure of your robot.

Configuration are written as Python dictionary so you can define/modify them programmatically. You can also import them form file such as JSON formatted file. In the configuration you have to define:

* controllers: For each defined controller, you can specify the port name, the attached motors and the synchronization mode.
* motors: You specify all motors belonging to your robot. You have to define their id, type, orientation, offset and angle_limit.
* motorgroups: It allows to define alias of group of motors. They can be nested.

"""
import warnings
import logging
import numpy
import time
import json

import pypot.robot
import pypot.dynamixel

from pypot.dynamixel.motor import DxlAXRXMotor, DxlMXMotor
from pypot.dynamixel.io import DxlError

ergo_robot_config = {
    'controllers': {
        'my_dxl_controller': {
            'port': '/dev/ttyUSB0',  # Depends on your OS
            'sync_read': False,
            'attached_motors': ['base', 'head'],  # You can mix motorgroups or individual motors
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
# This logger should always provides the config as extra
logger = logging.getLogger(__name__)


def from_config(config):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a configuration dictionnary.

        For details on how to write such a configuration dictionnary, you should refer to the section :ref:`config_file`.

        """
    logger.info('Loading config... ', extra={'config': config})
    robot = pypot.robot.Robot()

    alias = config['motorgroups']

    # Instatiate the different controllers
    for c_name, c_params in config['controllers'].items():
        dxl_io = pypot.dynamixel.DxlIO(port=c_params['port'],
                                       use_sync_read=c_params['sync_read'],
                                       error_handler_cls=pypot.dynamixel.BaseErrorHandler)

        dxl_motors = []
        motor_names = sum([_motor_extractor(alias, name) for name in c_params['attached_motors']], [])
        motor_nodes = map(lambda m: (m, config['motors'][m]), motor_names)

        # First, scan everyone to make sure that we are not missing any motors
        ids = [params['id'] for _, params in motor_nodes]
        found_ids = dxl_io.scan(ids)
        if ids != found_ids:
            missing_ids = tuple(set(ids) - set(found_ids))
            raise DxlError('Could not find the motors {} on bus {}.'.format(missing_ids,
                                                                            dxl_io.port))

        # Instatiate the attached motors and set their angle_limits if needed
        changed_angle_limits = {}
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
                logger.warning("Limits of '%s' changed to %s",
                               m.name, angle_limit,
                               extra={'config': config})
                changed_angle_limits[m.id] = angle_limit

            logger.info("Instantiating motor '%s' id=%d direct=%s limits=%s offset=%s",
                        m.name, m.id, m.direct, angle_limit, m.offset,
                        extra={'config': config})

        logger.info('Instantiating controller on %s with motors %s',
                    c_params['port'], motor_names,
                    extra={'config': config})

        if changed_angle_limits:
            dxl_io.set_angle_limit(changed_angle_limits)
            time.sleep(1)

        robot._attach_dxl_motors(dxl_io, dxl_motors)

    # Create the alias for the motorgroups
    for alias_name in alias.keys():
        motors = [getattr(robot, name) for name in _motor_extractor(alias, alias_name)]
        setattr(robot, alias_name, motors)
        robot.alias.append(alias_name)

        logger.info("Creating alias '%s' for motors %s",
                    alias_name, [m.name for m in motors],
                    extra={'config': config})

    logger.info('Loading complete!',
                extra={'config': config})

    return robot


def from_json(json_file):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a JSON configuration file.

    For details on how to write such a configuration file, you should refer to the section :ref:`config_file`.

    """
    with open(json_file) as f:
        config = json.load(f)

    return from_config(config)


def _oldxml_to_config(xml_file):
    msg = 'Using XML file as configuration is deprecated, you should switch to Python dictionnary. You can save them as any format that can directly be transformed into a dictionnary (e.g. json files).'

    warnings.warn(msg, DeprecationWarning)

    import xml.dom.minidom

    config = {}

    dom = xml.dom.minidom.parse(xml_file)
    robot_node = dom.firstChild

    config['controllers'] = {}
    for i, controller_node in enumerate(robot_node.getElementsByTagName('DxlController')):
        name = 'controller_{}'.format(i + 1)
        motors_node = controller_node.getElementsByTagName('DxlMotor')
        config['controllers'][name] = {'port': str(controller_node.getAttribute('port')),
                                       'sync_read': True if controller_node.getAttribute('sync_read') == 'True' else False,
                                       'attached_motors': [m.getAttribute('name') for m in motors_node]}

    config['motorgroups'] = {}
    for motor_group_node in robot_node.getElementsByTagName('DxlMotorGroup'):
        name = str(motor_group_node.getAttribute('name'))
        motors_node = motor_group_node.getElementsByTagName('DxlMotor')
        config['motorgroups'][name] = [str(m.getAttribute('name')) for m in motors_node]

    config['motors'] = {}
    for motor_node in robot_node.getElementsByTagName('DxlMotor'):
        name = str(motor_node.getAttribute('name'))
        angle_limit_node = motor_node.getElementsByTagName('angle_limits')[0]
        angle_limit = eval(angle_limit_node.firstChild.data)
        config['motors'][name] = {'id': int(motor_node.getAttribute('id')),
                                  'type': str(motor_node.getAttribute('type')),
                                  'orientation': str(motor_node.getAttribute('orientation')),
                                  'offset': float(motor_node.getAttribute('offset')),
                                  'angle_limit': angle_limit}

    logger.warning(msg, extra={'config': config})

    return config


def _motor_extractor(alias, name):
    l = []

    if name not in alias:
        return [name]

    for key in alias[name]:
        l += _motor_extractor(alias, key) if key in alias else [key]
    return l

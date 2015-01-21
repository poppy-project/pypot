"""
The config module allows the definition of the structure of your robot.

Configuration are written as Python dictionary so you can define/modify them programmatically. You can also import them form file such as JSON formatted file. In the configuration you have to define:

* controllers: For each defined controller, you can specify the port name, the attached motors and the synchronization mode.
* motors: You specify all motors belonging to your robot. You have to define their id, type, orientation, offset and angle_limit.
* motorgroups: It allows to define alias of group of motors. They can be nested.

"""
import logging
import numpy
import time
import json

import pypot.dynamixel
import pypot.dynamixel.io
import pypot.dynamixel.error
import pypot.dynamixel.motor
import pypot.dynamixel.controller

from .robot import Robot

# This logger should always provides the config as extra
logger = logging.getLogger(__name__)


def from_config(config, strict=True):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a configuration dictionnary.

        :param dict config: robot configuration dictionary
        :param bool strict: make sure that all ports, motors are availaible.

        For details on how to write such a configuration dictionnary, you should refer to the section :ref:`config_file`.

        """
    logger.info('Loading config... ', extra={'config': config})

    alias = config['motorgroups']

    # Instatiate the different motor controllers
    controllers = []
    for c_name, c_params in config['controllers'].items():
        motor_names = sum([_motor_extractor(alias, name)
                           for name in c_params['attached_motors']], [])

        attached_motors = [motor_from_confignode(config, name) for name in motor_names]

        # at least one of the motor is set as broken
        if [m for m in attached_motors if m._broken]:
            strict = False

        attached_ids = [m.id for m in attached_motors]
        dxl_io = dxl_io_from_confignode(config, c_params, attached_ids, strict)

        check_motor_limits(config, dxl_io, motor_names)

        c = pypot.dynamixel.controller.BaseDxlController(dxl_io, attached_motors)
        logger.info('Instantiating controller on %s with motors %s',
                    dxl_io.port, motor_names,
                    extra={'config': config})

        controllers.append(c)

    robot = Robot(motor_controllers=controllers)
    make_alias(config, robot)

    logger.info('Loading complete!',
                extra={'config': config})

    return robot


def motor_from_confignode(config, motor_name):
    params = config['motors'][motor_name]

    MotorCls = (pypot.dynamixel.motor.DxlMXMotor if params['type'].startswith('MX')
                else pypot.dynamixel.motor.DxlAXRXMotor)

    m = MotorCls(id=params['id'],
                 name=motor_name,
                 model=params['type'],
                 direct=True if params['orientation'] == 'direct' else False,
                 offset=params['offset'],
                 broken='broken' in params)

    logger.info("Instantiating motor '%s' id=%d direct=%s offset=%s",
                m.name, m.id, m.direct, m.offset,
                extra={'config': config})

    return m


def dxl_io_from_confignode(config, c_params, ids, strict):
    port = c_params['port']

    if port == 'auto':
        port = pypot.dynamixel.find_port(ids, strict)
        logger.info('Found port {} for ids {}'.format(port, ids))

    handler = pypot.dynamixel.error.BaseErrorHandler
    dxl_io = pypot.dynamixel.io.DxlIO(port=port,
                                      use_sync_read=c_params['sync_read'],
                                      error_handler_cls=handler)

    found_ids = dxl_io.scan(ids)
    if ids != found_ids:
        missing_ids = tuple(set(ids) - set(found_ids))
        msg = 'Could not find the motors {} on bus {}.'.format(missing_ids,
                                                               dxl_io.port)
        logger.warning(msg)

        if strict:
            raise pypot.dynamixel.io.DxlError(msg)

    return dxl_io


def check_motor_limits(config, dxl_io, motor_names):
    changed_angle_limits = {}

    for name in motor_names:
        m = config['motors'][name]
        id = m['id']

        try:
            old_limits = dxl_io.get_angle_limit((id, ))[0]
        except IndexError: # probably a broken motor so we just skip
            continue
        new_limits = m['angle_limit']

        d = numpy.linalg.norm(numpy.asarray(new_limits) - numpy.asarray(old_limits))
        if d > 1:
            logger.warning("Limits of '%s' changed to %s",
                           name, new_limits,
                           extra={'config': config})
            changed_angle_limits[id] = new_limits

    if changed_angle_limits:
        dxl_io.set_angle_limit(changed_angle_limits)
        time.sleep(1)


def instatiate_motors(config):
    motors = []

    for m_name, m_params in config['motors']:
        MotorCls = (pypot.dynamixel.motor.DxlMXMotor if m_params['type'].startswith('MX')
                    else pypot.dynamixel.motor.DxlAXRXMotor)

        m = MotorCls(id=m_params['id'],
                     name=m_name,
                     direct=True if m_params['orientation'] == 'direct' else False,
                     offset=m_params['offset'])

        motors.append(m)

        logger.info("Instantiating motor '%s' id=%d direct=%s offset=%s",
                    m.name, m.id, m.direct, m.offset,
                    extra={'config': config})

    return motors


def make_alias(config, robot):
    alias = config['motorgroups']

    # Create the alias for the motorgroups
    for alias_name in alias:
        motors = [getattr(robot, name) for name in _motor_extractor(alias, alias_name)]
        setattr(robot, alias_name, motors)
        robot.alias.append(alias_name)

        logger.info("Creating alias '%s' for motors %s",
                    alias_name, [motor.name for motor in motors],
                    extra={'config': config})


def from_json(json_file):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a JSON configuration file.

    For details on how to write such a configuration file, you should refer to the section :ref:`config_file`.

    """
    with open(json_file) as f:
        config = json.load(f)

    return from_config(config)


def _motor_extractor(alias, name):
    l = []

    if name not in alias:
        return [name]

    for key in alias[name]:
        l += _motor_extractor(alias, key) if key in alias else [key]
    return l

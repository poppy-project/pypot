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

from collections import OrderedDict

import pypot.sensor
import pypot.dynamixel
import pypot.dynamixel.io
import pypot.dynamixel.error
import pypot.dynamixel.motor
import pypot.dynamixel.syncloop

from .robot import Robot
from .controller import DummyController


# This logger should always provides the config as extra
logger = logging.getLogger(__name__)


def from_config(config, strict=True, sync=True, use_dummy_io=False):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a configuration dictionnary.

        :param dict config: robot configuration dictionary
        :param bool strict: make sure that all ports, motors are availaible.
        :param bool sync: choose if automatically starts the synchronization loops

        For details on how to write such a configuration dictionnary, you should refer to the section :ref:`config_file`.

        """
    logger.info('Loading config... ', extra={'config': config})

    alias = config['motorgroups']

    # Instatiate the different motor controllers
    controllers = []
    for c_name, c_params in config['controllers'].items():
        motor_names = sum([_motor_extractor(alias, name)
                           for name in c_params['attached_motors']], [])

        attached_motors = [motor_from_confignode(config, name)
                           for name in motor_names]

        # at least one of the motor is set as broken
        if [m for m in attached_motors if m._broken]:
            strict = False

        attached_ids = [m.id for m in attached_motors]
        if not use_dummy_io:
            dxl_io = dxl_io_from_confignode(config, c_params, attached_ids, strict)

            check_motor_eprom_configuration(config, dxl_io, motor_names)

            logger.info('Instantiating controller on %s with motors %s',
                        dxl_io.port, motor_names,
                        extra={'config': config})

            syncloop = (c_params['syncloop'] if 'syncloop' in c_params
                        else 'BaseDxlController')
            SyncLoopCls = getattr(pypot.dynamixel.syncloop, syncloop)

            c = SyncLoopCls(dxl_io, attached_motors)
            controllers.append(c)
        else:
            controllers.append(DummyController(attached_motors))

    robot = Robot(motor_controllers=controllers, sync=sync)
    make_alias(config, robot)

    # Create all sensors and attached them
    if 'sensors' in config and not use_dummy_io:
        sensors = []
        for s_name in config['sensors'].keys():
            sensor = sensor_from_confignode(config, s_name, robot)
            setattr(robot, s_name, sensor)
            sensors.append(sensor)

        robot.sensors.extend(sensors)
        [s.start() for s in sensors if hasattr(s, 'start')]

    logger.info('Loading complete!',
                extra={'config': config})

    return robot


def motor_from_confignode(config, motor_name):
    params = config['motors'][motor_name]

    type = params['type']
    if type == 'XL-320':
        MotorCls = pypot.dynamixel.motor.DxlXL320Motor
    elif type.startswith('MX'):
        MotorCls = pypot.dynamixel.motor.DxlMXMotor
    elif type.startswith('AX') or type.startswith('RX'):
        MotorCls = pypot.dynamixel.motor.DxlAXRXMotor

    broken = 'broken' in params and params['broken']

    m = MotorCls(id=params['id'],
                 name=motor_name,
                 model=type,
                 direct=True if params['orientation'] == 'direct' else False,
                 offset=params['offset'],
                 broken=broken)

    logger.info("Instantiating motor '%s' id=%d direct=%s offset=%s",
                m.name, m.id, m.direct, m.offset,
                extra={'config': config})

    return m


def sensor_from_confignode(config, s_name, robot):
    args = config['sensors'][s_name]
    cls_name = args.pop("type")

    if 'need_robot' in args and args.pop('need_robot'):
        args['robot'] = robot

    SensorCls = getattr(pypot.sensor, cls_name)
    return SensorCls(name=s_name, **args)


def dxl_io_from_confignode(config, c_params, ids, strict):
    port = c_params['port']

    if port == 'auto':
        port = pypot.dynamixel.find_port(ids, strict)
        logger.info('Found port {} for ids {}'.format(port, ids))

    sync_read = c_params['sync_read']

    if sync_read == 'auto':
        # USB Vendor Product ID "VID:PID=0403:6001" for USB2Dynamixel
        # USB Vendor Product ID "VID:PID=16d0:06a7" for USBAX
        vendor_pid = pypot.dynamixel.get_port_vendor_info(port)
        sync_read = ('PID=0403:6001' in vendor_pid and c_params['protocol'] == 2 or
                     'PID=16d0:06a7' in vendor_pid)
        logger.info('sync_read is {}. Vendor pid = {}'.format(sync_read, vendor_pid))

    handler = pypot.dynamixel.error.BaseErrorHandler

    DxlIOCls = (pypot.dynamixel.io.Dxl320IO
                if 'protocol' in c_params and c_params['protocol'] == 2
                else pypot.dynamixel.io.DxlIO)

    dxl_io = DxlIOCls(port=port,
                      use_sync_read=sync_read,
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


def check_motor_eprom_configuration(config, dxl_io, motor_names):
    """ Change the angles limits depanding on the robot configuration ;
        Check if the return delay time is set to 0.
    """
    changed_angle_limits = {}
    changed_return_delay_time = {}

    for name in motor_names:
        m = config['motors'][name]
        id = m['id']

        try:
            old_limits = dxl_io.get_angle_limit((id, ))[0]
            old_return_delay_time = dxl_io.get_return_delay_time((id, ))[0]
        except IndexError:  # probably a broken motor so we just skip
            continue

        if old_return_delay_time != 0:
            logger.warning("Return delay time of %s changed from %s to 0",
                           name, old_return_delay_time)
            changed_return_delay_time[id] = 0

        new_limits = m['angle_limit']
        d = numpy.linalg.norm(numpy.asarray(new_limits) - numpy.asarray(old_limits))
        if d > 1:
            logger.warning("Limits of '%s' changed from %s to %s",
                           name, old_limits, new_limits,
                           extra={'config': config})
            changed_angle_limits[id] = new_limits

    if changed_angle_limits:
        dxl_io.set_angle_limit(changed_angle_limits)
        time.sleep(0.5)

    if changed_return_delay_time:
        dxl_io.set_return_delay_time(changed_return_delay_time)
        time.sleep(0.5)


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


def from_json(json_file, sync=True, strict=True, use_dummy_io=False):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a JSON configuration file.

    For details on how to write such a configuration file, you should refer to the section :ref:`config_file`.

    """
    with open(json_file) as f:
        config = json.load(f, object_pairs_hook=OrderedDict)

    return from_config(config, sync=sync, strict=strict, use_dummy_io=use_dummy_io)


def use_dummy_robot(json_file):
    return from_json(json_file, use_dummy_io=True)


def _motor_extractor(alias, name):
    l = []

    if name not in alias:
        return [name]

    for key in alias[name]:
        l += _motor_extractor(alias, key) if key in alias else [key]
    return l


ergo_robot_config = {
    'controllers': {
        'my_dxl_controller': {
            'sync_read': False,
            'attached_motors': ['base', 'tip'],
            'port': 'auto'
        }
    },
    'motorgroups': {
        'base': ['m1', 'm2', 'm3'],
        'tip': ['m4', 'm5', 'm6']
    },
    'motors': {
        'm5': {
            'orientation': 'indirect',
            'type': 'MX-28',
            'id': 15,
            'angle_limit': [-90.0, 90.0],
            'offset': 0.0
        },
        'm4': {
            'orientation': 'direct',
            'type': 'MX-28',
            'id': 14,
            'angle_limit': [-90.0, 90.0],
            'offset': 0.0
        },
        'm6': {
            'orientation': 'indirect',
            'type': 'MX-28',
            'id': 16,
            'angle_limit': [-90.0, 90.0],
            'offset': 0.0
        },
        'm1': {
            'orientation': 'direct',
            'type': 'MX-28', 'id': 11,
            'angle_limit': [-90.0, 90.0],
            'offset': 0.0
        },
        'm3': {
            'orientation': 'indirect',
            'type': 'MX-28',
            'id': 13,
            'angle_limit': [-90.0, 90.0],
            'offset': 0.0
        },
        'm2': {
            'orientation': 'indirect',
            'type': 'MX-28',
            'id': 12,
            'angle_limit': [-90.0, 90.0],
            'offset': 0.0
        }
    }
}

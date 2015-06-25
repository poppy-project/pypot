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
import platform

#manufacturer-specific stuff
import pypot.herkulex.io
import pypot.herkulex.error
import pypot.herkulex.motor
import pypot.herkulex.controller

import pypot.dynamixel
import pypot.dynamixel.io
import pypot.dynamixel.error
import pypot.dynamixel.motor
import pypot.dynamixel.controller

from .robot import Robot

# This logger should always provides the config as extra
logger = logging.getLogger(__name__)


def from_config(config, strict=True, possible_ports=None, sync=True):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a configuration dictionnary.

        :param dict config: robot configuration dictionary
        :param bool strict: make sure that all ports, motors are availaible.
        :param bool sync: choose if automatically starts the synchronization loops
        :param dictionary possible_ports: dictionary giving, for each manufacturer, a list of ports where the motors should be looked for if not already specified in the config
        if the port is not specified in the config and possible_port is None, then all serial ports can be scanned (possibly causing a mess)
        example of syntax for possible_ports: {'Herkulex' : ('COM4',),'Dynamixel' : ('COM3',)}
        For details on how to write such a configuration dictionnary, you should refer to the section :ref:`config_file`.

        """
    logger.info('Loading config... ', extra={'config': config})

    alias = config['motorgroups']

    # Instantiate the different motor controllers
    controllers = []
    for c_name, c_params in config['controllers'].items():
        motor_names = sum([_motor_extractor(alias, name)
                           for name in c_params['attached_motors']], [])
        #autodetect the manufacturer based on motor type
        manufacturer = None
        if all(config['motors'][mn]['type'] in pypot.dynamixel.conversion.dynamixelModels.values() for mn in motor_names):
            manufacturer = 'Dynamixel'
        elif all(config['motors'][mn]['type'] in pypot.herkulex.conversion.herkulexModels.values() for mn in motor_names):
            manufacturer = 'Herkulex'
        #set manufacturer-specific functions and classes
        if manufacturer == 'Herkulex':
            function_motor_from_confignode = hkx_motor_from_confignode
            ioCls=pypot.herkulex.io.HkxIO
            controllerCls = pypot.herkulex.BaseHkxController
            handlerCls = pypot.herkulex.HkxBaseErrorHandler
        elif manufacturer == 'Dynamixel':
            function_motor_from_confignode = dxl_motor_from_confignode
            ioCls= (pypot.dynamixel.io.Dxl320IO
                if 'protocol' in c_params and c_params['protocol'] == 2
                else pypot.dynamixel.io.DxlIO)
            controllerCls = pypot.dynamixel.BaseDxlController
            handlerCls = pypot.dynamixel.BaseErrorHandler
        else:
            raise Exception('Unable to recognize a single manufacturer for motors %s in controller %s' %(motor_names, c_name))

        attached_motors = [function_motor_from_confignode(config, name)
                           for name in motor_names]

        # at least one of the motor is set as broken
        if [m for m in attached_motors if m._broken]:
            strict = False
        poss_ports = None
        #if the port is to be auto-detected check if it should only be among certain ports 
        if c_params['port'] == 'auto':
            if possible_ports != None:
                if manufacturer in possible_ports:
                    poss_ports = possible_ports[manufacturer]
        attached_ids = [m.id for m in attached_motors]
        io = io_from_confignode(config, c_params, attached_ids, strict, ioCls, poss_ports, handlerCls)

        check_motor_limits(config, io, motor_names)

        c = controllerCls(io, attached_motors)
        logger.info('Instantiating controller on %s with motors %s',
                    io.port, motor_names,
                    extra={'config': config})

        controllers.append(c)

    robot = Robot(motor_controllers=controllers, sync=sync)
    make_alias(config, robot)

    logger.info('Loading complete!',
                extra={'config': config})

    return robot

#just changed the name by adding 'dxl_' in front to make it clearly dxl-specific
def dxl_motor_from_confignode(config, motor_name):
    params = config['motors'][motor_name]

    type = params['type']
    if type == 'XL-320':
        MotorCls = pypot.dynamixel.motor.DxlXL320Motor
    elif type.startswith('MX'):
        MotorCls = pypot.dynamixel.motor.DxlMXMotor
    elif type.startswith('AX') or type.startswith('RX'):
        MotorCls = pypot.dynamixel.motor.DxlAXRXMotor

    m = MotorCls(id=params['id'],
                 name=motor_name,
                 model=type,
                 direct=True if params['orientation'] == 'direct' else False,
                 offset=params['offset'],
                 broken='broken' in params)

    logger.info("Instantiating motor '%s' id=%d direct=%s offset=%s",
                m.name, m.id, m.direct, m.offset,
                extra={'config': config})

    return m

#new function for herkulex
def hkx_motor_from_confignode(config, motor_name):
    params = config['motors'][motor_name]
    m = pypot.herkulex.motor.HkxMotor(id=params['id'],
                 name=motor_name,
                 model=params['type'],
                 direct=True if params['orientation'] == 'direct' else False,
                 offset=params['offset'],
                 broken='broken' in params)

    logger.info("Instantiating motor '%s' id=%d direct=%s offset=%s",
                m.name, m.id, m.direct, m.offset,
                extra={'config': config})

    return m

#'universal' version of the original function (including for error handler)
def io_from_confignode(config, c_params, ids, strict, ioCls, poss_ports, handlerCls):
    port = c_params['port']

    if port == 'auto':
        port = find_port(ids, ioCls, strict, poss_ports)
        logger.info('Found port {} for ids {}'.format(port, ids))

    io = ioCls(port=port,
                      use_sync_read=c_params['sync_read'],
                      error_handler_cls=handlerCls)

    found_ids = io.scan(ids)
    if ids != found_ids:
        missing_ids = tuple(set(ids) - set(found_ids))
        msg = 'Could not find the motors {} on bus {}.'.format(missing_ids,
                                                               io.port)
        logger.warning(msg)

        if strict:
            raise Exception(msg)

    return io


def check_motor_limits(config, io, motor_names):
    changed_angle_limits = {}

    for name in motor_names:
        m = config['motors'][name]
        id = m['id']

        try:
            old_limits = io.get_angle_limit((id, ))[0]
        except IndexError:  # probably a broken motor so we just skip
            continue
        new_limits = m['angle_limit']

        d = numpy.linalg.norm(numpy.asarray(new_limits) - numpy.asarray(old_limits))
        if d > 1:
            logger.warning("Limits of '%s' changed to %s",
                           name, new_limits,
                           extra={'config': config})
            changed_angle_limits[id] = new_limits

    if changed_angle_limits:
        io.set_angle_limit(changed_angle_limits)
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

#'universal' version of the original function to support mixed motor manufacturers, even within the same robot (but no mix within a controller)
def from_json(json_file, possible_ports = None, sync=True):
    """ Returns a :class:`~pypot.robot.robot.Robot` instance created from a JSON configuration file.

    For details on how to write such a configuration file, you should refer to the section :ref:`config_file`.

    """
    with open(json_file) as f:
        config = json.load(f)

    return from_config(config, possible_ports=possible_ports, sync=sync)


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

#just taken from pypot/dynamixel/__init__.py
def get_available_ports():
    """ Tries to find the available usb2serial port on your system. """
    if platform.system() == 'Darwin':
        return glob.glob('/dev/tty.usb*')

    elif platform.system() == 'Linux':
        return glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

    elif platform.system() == 'Windows':
        import _winreg
        import itertools

        ports = []
        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)

        for i in itertools.count():
            try:
                ports.append(str(_winreg.EnumValue(key, i)[1]))
            except WindowsError:
                return ports

    return []

#taken from dynamixel __init__.py and extended to support mixed motor manufacturers
def find_port(ids, ioCls, strict=True, poss_ports=None):
    """ Find the port with the specified attached motor ids.

        :param list ids: list of motor ids to find
        :param bool strict: specify if all ids should be find (when set to False, only half motor must be found)
        :param poss_ports: used to restrict the search
        .. warning:: If two (or more) ports are attached to the same list of motor ids the first match will be returned.

    """
    for port in get_available_ports():
        if poss_ports == None or port in poss_ports:
            try:
                with ioCls(port) as io_sc:
                    founds = len(io_sc.scan(ids))
    
                    if strict and founds == len(ids):
                        return port
    
                    if not strict and founds >= len(ids) / 2:
                        return port
            except HkxError:
                continue

    raise IndexError('No suitable port found for ids {}!'.format(ids))

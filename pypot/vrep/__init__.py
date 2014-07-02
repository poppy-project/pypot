from .io import (VrepIO, close_all_connections,
                 VrepIOError, VrepConnectionError)

from .controller import VrepController

from ..robot import Robot
from ..robot.config import motor_from_confignode


def from_vrep(config, vrep_host, vrep_port):
    """ Create a robot from a V-REP instance.

    This function tries to connect to a V-REP instance and expects to find motors with names corresponding as the ones found in the config.

    .. note:: Using the same configuration, you should be able to switch from a real to a simulated robot just by switching from :func:`~pypot.robot.config.from_config` to :func:`~pypot.vrep.from_vrep`.
        For instance::

            import json

            with open('my_config.json') as f:
                config = json.load(f)

            from pypot.robot import from_config
            from pypot.vrep import from_vrep

            real_robot = from_config(config)
            simulated_robot = from_vrep(config, '127.0.0.1', 19997)

    """
    motors = [motor_from_confignode(config, name) for name in config['motors'].keys()]
    controller = VrepController(vrep_host, vrep_port, motors)

    return Robot(motor_controllers=[controller])

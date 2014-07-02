from .io import (VrepIO, close_all_connections,
                 VrepIOError, VrepConnectionError)

from .controller import VrepController

from ..robot import Robot
from ..robot.config import motor_from_confignode


def from_vrep(config, vrep_host, vrep_port):
    motors = [motor_from_confignode(config, name) for name in config['motors'].keys()]
    controller = VrepController(vrep_host, vrep_port, motors)

    return Robot(motor_controllers=[controller])

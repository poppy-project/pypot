from .io import (VrepIO, close_all_connections,
                 VrepIOError, VrepConnectionError)

from .controller import VrepController, VrepObjectTracker

from ..robot import Robot
from ..robot.sensor import ObjectTracker
from ..robot.config import motor_from_confignode, make_alias


def from_vrep(config, vrep_host, vrep_port, vrep_scene, tracked_objects=[]):
    """ Create a robot from a V-REP instance.

    :param dict config: robot configuration dictionary
    :param str vrep_host: host of the V-REP server
    :param int vrep_port: port of the V-REP server
    :param str vrep_scene: path to the V-REP scene to load and start
    :param list tracked_objects: list of V-REP dummy object to track

    This function tries to connect to a V-REP instance and expects to find motors with names corresponding as the ones found in the config.

    The :class:`~pypot.robot.robot.Robot` returned will also provide a conveniencd reset_simulation method which resets the simulation and the robot position to its intial stance.

    .. note:: Using the same configuration, you should be able to switch from a real to a simulated robot just by switching from :func:`~pypot.robot.config.from_config` to :func:`~pypot.vrep.from_vrep`.
        For instance::

            import json

            with open('my_config.json') as f:
                config = json.load(f)

            from pypot.robot import from_config
            from pypot.vrep import from_vrep

            real_robot = from_config(config)
            simulated_robot = from_vrep(config, '127.0.0.1', 19997, 'poppy.ttt')

    """
    vrep_io = VrepIO(vrep_host, vrep_port)

    motors = [motor_from_confignode(config, name) for name in config['motors'].keys()]
    vc = VrepController(vrep_io, vrep_scene, motors)

    sensor_controller = []
    if tracked_objects:
        sensors = [ObjectTracker(name) for name in tracked_objects]
        vot = VrepObjectTracker(vrep_io, sensors)
        sensor_controller.append(vot)

    robot = Robot(motor_controllers=[vc],
                  sensor_controllers=sensor_controller)

    init_pos = {m: m.present_position for m in robot.motors}

    make_alias(config, robot)

    def reset(robot):
        for m, p in init_pos.iteritems():
            m.goal_position = p

        robot._controllers[0].io.restart_simulation()

    robot.reset_simulation = lambda: reset(robot)

    return robot

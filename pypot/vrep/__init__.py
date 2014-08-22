from .io import (VrepIO, close_all_connections,
                 VrepIOError, VrepConnectionError)

from .controller import VrepController, VrepObjectTracker
from .controller import VrepCollisionTracker, VrepCollisionDetector

from ..robot import Robot
from ..robot.sensor import ObjectTracker
from ..robot.config import motor_from_confignode, make_alias


import pypot.utils.pypot_time as pypot_time
import time as sys_time
import vrep

ROBOT = None


class vrep_time():
    def __init__(self, robot):
        self.robot = robot

    def get_time(self):
        # print 'CUSTOM TIME'
        # return self.robot._controllers[0].io.get_simulation_current_time()
        res, tt = vrep.simxGetFloatSignal(self.robot._controllers[0].io.client_id, 'CurrentTime', vrep.simx_opmode_buffer)
        return tt

    def sleep(self, t):
        t0 = self.get_time()
        while (self.get_time() - t0) < t:
            sys_time.sleep(0.01)





def from_vrep(config, vrep_host, vrep_port, vrep_scene,
              tracked_objects=[], tracked_collisions=[]):
    """ Create a robot from a V-REP instance.

    :param dict config: robot configuration dictionary
    :param str vrep_host: host of the V-REP server
    :param int vrep_port: port of the V-REP server
    :param str vrep_scene: path to the V-REP scene to load and start
    :param list tracked_objects: list of V-REP dummy object to track
    :param list tracked_collisions: list of V-REP collision to track

    This function tries to connect to a V-REP instance and expects to find motors with names corresponding as the ones found in the config.

    .. note:: The :class:`~pypot.robot.robot.Robot` returned will also provide a convenience reset_simulation method which resets the simulation and the robot position to its intial stance.

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

    # The URDF uses the offset as the 0 for the motors equivalent
    # so we set all the offsets to 0    config = dict(config)
    for m in config['motors'].itervalues():
        m['offset'] = 0.0

    motors = [motor_from_confignode(config, name) for name in config['motors'].keys()]
    vc = VrepController(vrep_io, vrep_scene, motors)
    vc._init_vrep_streaming()

    sensor_controllers = []

    if tracked_objects:
        sensors = [ObjectTracker(name) for name in tracked_objects]
        vot = VrepObjectTracker(vrep_io, sensors)
        sensor_controllers.append(vot)

    if tracked_collisions:
        sensors = [VrepCollisionDetector(name) for name in tracked_collisions]
        vct = VrepCollisionTracker(vrep_io, sensors)
        sensor_controllers.append(vct)

    robot = Robot(motor_controllers=[vc],
                  sensor_controllers=sensor_controllers)

    init_pos = {m: m.goal_position for m in robot.motors}

    make_alias(config, robot)

    def reset(robot):
        for m, p in init_pos.iteritems():
            m.goal_position = p

        if tracked_collisions:
            vct.stop()

        vrep_io.restart_simulation()

        if tracked_collisions:
            vct.start()

    robot.reset_simulation = lambda: reset(robot)

    def current_simulation_time(robot):
        return robot._controllers[0].io.get_simulation_current_time()

    Robot.current_simulation_time = property(lambda robot: current_simulation_time(robot))

    res, tt = vrep.simxGetFloatSignal(robot._controllers[0].io.client_id, 'CurrentTime', vrep.simx_opmode_streaming)
    vreptime = vrep_time(robot)
    pypot_time.time = vreptime.get_time
    # pypot_time.sleep = vreptime.sleep

    return robot

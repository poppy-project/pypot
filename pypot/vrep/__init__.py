import json
import logging

from functools import partial
from collections import OrderedDict

from .io import (VrepIO, close_all_connections,
                 VrepIOError, VrepConnectionError)

from .controller import VrepController, VrepObjectTracker
from .controller import VrepCollisionTracker, VrepCollisionDetector

from ..robot import Robot
from ..robot.sensor import ObjectTracker
from ..robot.config import motor_from_confignode, make_alias


import pypot.utils.pypot_time as pypot_time
import time as sys_time

logger = logging.getLogger(__name__)


class vrep_time():
    def __init__(self, vrep_io):
        self.io = vrep_io

    def get_time(self, trial=0):
        t = self.io.get_simulation_current_time()

        if t == 0:
            sys_time.sleep(.5)
            return self.get_time(trial + 1)

        if trial > 10:
            raise EnvironmentError('Could not get current simulation time. Make sure the V-REP simulation is running. And that you have added the "time" child script to your scene.')

        return t

    def sleep(self, t):
        if t > 1000:  # That's probably due to an error in get_time
            logger.warning('Big vrep sleep: {}'.format(t))
            t = 1

        t0 = self.get_time()
        while (self.get_time() - t0) < t:
            if self.get_time() < t0:
                break
            sys_time.sleep(0.01)


def from_vrep(config, vrep_host='127.0.0.1', vrep_port=19997, scene=None,
              tracked_objects=[], tracked_collisions=[]):
    """ Create a robot from a V-REP instance.

    :param config: robot configuration (either the path to the json or directly the dictionary)
    :type config: str or dict
    :param str vrep_host: host of the V-REP server
    :param int vrep_port: port of the V-REP server
    :param str scene: path to the V-REP scene to load and start
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

    vreptime = vrep_time(vrep_io)
    pypot_time.time = vreptime.get_time
    pypot_time.sleep = vreptime.sleep

    if isinstance(config, basestring):
        with open(config) as f:
            config = json.load(f, object_pairs_hook=OrderedDict)

    motors = [motor_from_confignode(config, name)
              for name in config['motors'].keys()]

    vc = VrepController(vrep_io, scene, motors)
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

    for m in robot.motors:
        m.goto_behavior = 'minjerk'

    init_pos = {m: m.goal_position for m in robot.motors}

    make_alias(config, robot)

    def start_simu():
        vrep_io.start_simulation()

        for m, p in init_pos.iteritems():
            m.goal_position = p

        vc.start()

        if tracked_objects:
            vot.start()

        if tracked_collisions:
            vct.start()

        while vrep_io.get_simulation_current_time() < 1.:
            sys_time.sleep(0.1)

    def stop_simu():
        if tracked_objects:
            vot.stop()

        if tracked_collisions:
            vct.stop()

        vc.stop()
        vrep_io.stop_simulation()

    def reset_simu():
        stop_simu()
        sys_time.sleep(0.5)
        start_simu()

    robot.start_simulation = start_simu
    robot.stop_simulation = stop_simu
    robot.reset_simulation = reset_simu

    def current_simulation_time(robot):
        return robot._controllers[0].io.get_simulation_current_time()
    Robot.current_simulation_time = property(lambda robot: current_simulation_time(robot))

    def get_object_position(robot, object, relative_to_object=None):
        return vrep_io.get_object_position(object, relative_to_object)
    Robot.get_object_position = partial(get_object_position, robot)

    def get_object_orientation(robot, object, relative_to_object=None):
        return vrep_io.get_object_orientation(object, relative_to_object)
    Robot.get_object_orientation = partial(get_object_orientation, robot)

    return robot

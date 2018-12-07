from __future__ import print_function

import sys
import logging
import json
import os
import re

from threading import Thread

from pypot.robot import Robot, from_json, use_dummy_robot
from pypot.server.snap import SnapRobotServer, find_local_ip

logger = logging.getLogger(__name__)

MAX_SETUP_TRIALS = 10


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def camelcase_to_underscore(name):
    return re.sub('([a-z])([A-Z0-9])', r'\1_\2', name).lower()


class AbstractPoppyCreature(Robot):
    """ Abstract Class for Any Poppy Creature. """
    def __new__(cls,
                base_path=None, config=None,
                simulator=None, scene=None, host='localhost', port=19997, id=None, shared_vrep_io=None,
                use_snap=False, snap_host='0.0.0.0', snap_port=6969, snap_quiet=True,
                use_http=False, http_host='0.0.0.0', http_port=8080, http_quiet=True,
                use_remote=False, remote_host='0.0.0.0', remote_port=4242,
                use_ws=False, ws_host='0.0.0.0', ws_port=9009,
                start_background_services=True, sync=True,
                **extra):
        """ Poppy Creature Factory.

        Creates a Robot (real or simulated) and specifies it to make it a specific Poppy Creature.

        :param str config: path to a specific json config (if None uses the default config of the poppy creature - e.g. poppy_humanoid.json)

        :param str simulator: name of the simulator used : 'vrep', 'poppy-simu', or 'dummy-robot'
        :param str scene: specify a particular simulation scene (if None uses the default scene of the poppy creature, use "keep-existing" to keep the current VRep scene - e.g. poppy_humanoid.ttt)
        :param str host: host of the simulator
        :param int port: port of the simulator
        :param int id: robot id in simulator (useful when using a scene with multiple robots)
        :param vrep_io: use an already connected VrepIO (useful when using a scene with multiple robots)
        :type vrep_io: :class:`~pypot.vrep.io.VrepIO`
        :param bool use_snap: start or not the Snap! API
        :param str snap_host: host of Snap! API
        :param int snap_port: port of the Snap!
        :param bool use_http: start or not the HTTP API
        :param str http_host: host of HTTP API
        :param int http_port: port of the HTTP API
        :param int id: id of robot in the v-rep scene (not used yet!)
        :param bool sync: choose if automatically starts the synchronization loops

        You can also add extra keyword arguments to disable sensor. For instance, to use a DummyCamera, you can add the argument: camera='dummy'.

        .. warning:: You can not specify a particular config when using a simulated robot!

        """
        if config and simulator:
            raise ValueError('Cannot set a specific config '
                             'when using a simulated version!')

        creature = camelcase_to_underscore(cls.__name__)
        base_path = (os.path.dirname(__import__(creature).__file__)
                     if base_path is None else base_path)

        default_config = os.path.join(os.path.join(base_path, 'configuration'),
                                      '{}.json'.format(creature))

        if config is None:
            config = default_config

        if simulator is not None:
            if simulator == 'vrep':
                from pypot.vrep import from_vrep, VrepConnectionError

                scene_path = os.path.join(base_path, 'vrep-scene')
                if scene != "keep-existing":
                    if scene is None:
                        scene = '{}.ttt'.format(creature)

                    elif not os.path.exists(scene):
                        if ((os.path.basename(scene) != scene) or
                                (not os.path.exists(os.path.join(scene_path, scene)))):
                            raise ValueError('Could not find the scene "{}"!'.format(scene))

                    scene = os.path.join(scene_path, scene)
                # TODO: use the id so we can have multiple poppy creatures
                # inside a single vrep scene

                # vrep.simxStart no longer listen on localhost
                if host == 'localhost':
                    host = '127.0.0.1'

                try:
                    poppy_creature = from_vrep(config, host, port, scene if scene != "keep-existing" else None, id=id, shared_vrep_io=shared_vrep_io)
                except VrepConnectionError:
                    raise IOError('Connection to V-REP failed!')

            elif simulator == 'poppy-simu':
                use_http = True
                poppy_creature = use_dummy_robot(config)
            elif simulator == 'dummy':
                poppy_creature = use_dummy_robot(config)
            else:
                raise ValueError('Unknown simulation mode: "{}"'.format(simulator))

            poppy_creature.simulated = True

        else:
            for _ in range(MAX_SETUP_TRIALS):
                try:
                    poppy_creature = from_json(config, sync, **extra)
                    logger.info('Init successful')
                    break
                except Exception as e:
                    logger.warning('Init fail: {}'.format(str(e)))
                    exc_type, exc_inst, tb = sys.exc_info()

            else:
                raise OSError('Could not initalize robot: {} '.format(exc_inst))
            poppy_creature.simulated = False

        with open(config) as f:
            poppy_creature.config = json.load(f)

        urdf_file = os.path.join(os.path.join(base_path,
                                              '{}.urdf'.format(creature)))
        poppy_creature.urdf_file = urdf_file

        if use_snap:
            poppy_creature.snap = SnapRobotServer(
                poppy_creature, snap_host, snap_port, quiet=snap_quiet)
            snap_url = 'http://snap.berkeley.edu/snapsource/snap.html'
            block_url = 'http://{}:{}/snap-blocks.xml'.format(find_local_ip(), snap_port)
            url = '{}#open:{}'.format(snap_url, block_url)
            logger.info('SnapRobotServer is now running on: http://{}:{}\n'.format(snap_host, snap_port))
            logger.info('You can open Snap! interface with loaded blocks at "{}"\n'.format(url))

        if use_http:
            from pypot.server.httpserver import HTTPRobotServer
            poppy_creature.http = HTTPRobotServer(poppy_creature, http_host, http_port,
                                                  cross_domain_origin="*", quiet=http_quiet)
            logger.info('HTTPRobotServer is now running on: http://{}:{}\n'.format(http_host, http_port))

        if use_remote:
            from pypot.server import RemoteRobotServer
            poppy_creature.remote = RemoteRobotServer(poppy_creature, remote_host, remote_port)
            logger.info('RemoteRobotServer is now running on: http://{}:{}\n'.format(remote_host, remote_port))

        if use_ws:
            from pypot.server import WsRobotServer
            poppy_creature.ws = WsRobotServer(poppy_creature, ws_host, ws_port)
            logger.info('Ws server is now running on: ws://{}:{}\n'.format(ws_host, ws_port))

        cls.setup(poppy_creature)

        if start_background_services:
            cls.start_background_services(poppy_creature)

        return poppy_creature

    @classmethod
    def start_background_services(cls, robot, services=['snap', 'http', 'remote', 'ws']):
        for service in services:
            if hasattr(robot, service):
                s = Thread(target=getattr(robot, service).run,
                           name='{}_server'.format(service))
                s.daemon = True
                s.start()
                logger.info("Starting {} service".format(service))

    @classmethod
    def setup(cls, robot):
        """ Classmethod used to specify your poppy creature.

        This is where you should attach any specific primitives for instance.

        """
        pass

    @classproperty
    @classmethod
    def default_config(cls):
        creature = camelcase_to_underscore(cls.__name__)
        base_path = os.path.dirname(__import__(creature).__file__)

        default_config = os.path.join(os.path.join(base_path, 'configuration'),
                                      '{}.json'.format(creature))

        with open(default_config) as f:
            return json.load(f)

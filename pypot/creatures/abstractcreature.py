from __future__ import print_function

import logging
import json
import os
import re

from threading import Thread

from pypot.robot import Robot, from_json, use_dummy_robot
from pypot.server import HttpAPIServer


logger = logging.getLogger(__name__)


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def camelcase_to_underscore(name):
    return re.sub('([a-z])([A-Z0-9])', r'\1_\2', name).lower()


class AbstractPoppyCreature(Robot):
    """ Abstract Class for Any Poppy Creature. """
    def __new__(cls,
                base_path=None, config=None,
                simulator=None, scene=None, host='localhost', port=19997, id=0,
                serve_http_api=True, http_api_host='0.0.0.0', http_api_port=6969, http_api_debug=False,
                use_remote=False, remote_host='0.0.0.0', remote_port=4242,
                start_background_services=True, sync=True,
                **extra):
        """ Poppy Creature Factory.

        Creates a Robot (real or simulated) and specifies it to make it a specific Poppy Creature.

        :param str config: path to a specific json config (if None uses the default config of the poppy creature - e.g. poppy_humanoid.json)

        :param str simulator: name of the simulator used : 'vrep' or 'poppy-simu'
        :param str scene: specify a particular simulation scene (if None uses the default scene of the poppy creature - e.g. poppy_humanoid.ttt)
        :param str host: host of the simulator
        :param int port: port of the simulator
        :param int id: id of robot in the v-rep scene (not used yet!)
        :param bool serve_http_api: start or not the HTTP API
        :param str http_api_host: host of HTTP API
        :param int http_api_port: port of the HTTP
        :param bool http_api_debug: set Flask debug mode
        :param bool use_remote: starts the zerorpc remote robot
        :param str remote_host: host of the remote robot server
        :param int remote_port: port of the remote robot server
        :param bool start_background_services: starts automatically all backgroud services (http api, remote)
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

                if scene is None:
                    scene = '{}.ttt'.format(creature)

                if not os.path.exists(scene):
                    if ((os.path.basename(scene) != scene) or
                            (not os.path.exists(os.path.join(scene_path, scene)))):
                        raise ValueError('Could not find the scene "{}"!'.format(scene))

                    scene = os.path.join(scene_path, scene)
                # TODO: use the id so we can have multiple poppy creatures
                # inside a single vrep scene
                try:
                    poppy_creature = from_vrep(config, host, port, scene)
                except VrepConnectionError:
                    raise IOError('Connection to V-REP failed!')

            elif simulator == 'poppy-simu':
                serve_http_api = True
                poppy_creature = use_dummy_robot(config)
            else:
                raise ValueError('Unknown simulation mode: "{}"'.format(simulator))

            poppy_creature.simulated = True

        else:
            try:
                poppy_creature = from_json(config, sync, **extra)
            except IndexError as e:
                raise IOError('Connection to the robot failed! {}'.format(str(e)))
            poppy_creature.simulated = False

        with open(config) as f:
            poppy_creature.config = json.load(f)

        urdf_file = os.path.join(os.path.join(base_path,
                                              '{}.urdf'.format(creature)))
        poppy_creature.urdf_file = urdf_file

        if serve_http_api:
            poppy_creature.http_api_server = HttpAPIServer(
                robot=poppy_creature,
                host=http_api_host, port=http_api_port,
                debug=http_api_debug
            )

        if use_remote:
            from pypot.server import RemoteRobotServer
            poppy_creature.remote = RemoteRobotServer(poppy_creature, remote_host, remote_port)
            print('RemoteRobotServer is now running on: http://{}:{}\n'.format(remote_host, remote_port))

        cls.setup(poppy_creature)

        if start_background_services:
            cls.start_background_services(poppy_creature)

        return poppy_creature

    @classmethod
    def start_background_services(cls, robot, services=['http_api_server', 'remote']):
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

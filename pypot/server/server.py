from .rest import RESTRobot

import logging

logger = logging.getLogger(__name__)


class AbstractServer(object):
    def __init__(self, robot, host, port):
        self.restful_robot = RESTRobot(robot)
        self.host, self.port = host, port

    def run(self):
        raise NotImplementedError


class RemoteRobotServer(AbstractServer):
    def run(self):
        try:
            import zerorpc
            server = zerorpc.Server(self.restful_robot)
            server.bind('tcp://{}:{}'.format(self.host, self.port))
            server.run()
        except ImportError:
            logger.warning(("Warning: The Python module 'zerorpc' is not installed. "
                            "Therefore the feature RemoteRobotServer is disabled. "
                            "On most systems this module can be installed with the command 'pip install zerorpc'."))

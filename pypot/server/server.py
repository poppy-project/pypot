from .rest import RESTRobot


class AbstractServer(object):
    def __init__(self, robot, host, port):
        self.restful_robot = RESTRobot(robot)
        self.host, self.port = host, port

    def run(self):
        raise NotImplementedError


try:
    import zerorpc

    class RemoteRobotServer(AbstractServer):
        def run(self):
            server = zerorpc.Server(self.restful_robot)
            server.bind('tcp://{}:{}'.format(self.host, self.port))
            server.run()

except ImportError:
    pass

import zmq
import json
import logging

from .server import AbstractServer


logger = logging.getLogger(__name__)


class ZMQRobotServer(AbstractServer):
    def __init__(self, robot, host, port):
        """ A ZMQServer allowing remote access of a robot instance.

        The server used the REQ/REP zmq pattern. You should always first send a request and then read the answer.

        """
        AbstractServer.__init__(self, robot, host, port)

        c = zmq.Context()
        self.socket = c.socket(zmq.REP)
        self.socket.bind('tcp://{}:{}'.format(self.host, self.port))

        logger.info('Starting ZMQServer on tcp://%s:%s', self.host, self.port)

    def run(self):
        """ Run an infinite REQ/REP loop. """
        while True:
            req = self.socket.recv_json()

            try:
                answer = self.handle_request(req)
                self.socket.send(json.dumps(answer))

            except (AttributeError, TypeError) as e:
                self.socket.send_json({'error': str(e)})

    def handle_request(self, request):
        meth_name, kwargs = request['robot'].popitem()
        meth = getattr(self.restful_robot, meth_name)

        for key in ('value', 'args'):
            if key in kwargs:
                kwargs[key] = json.loads(kwargs[key])

        ret = meth(**kwargs)
        ret = {} if ret is None else ret

        return ret

import zmq
import json
import logging

from .server import AbstractServer, MyJSONEncoder


logger = logging.getLogger(__name__)


class ZMQServer(AbstractServer):
    def __init__(self, robot, host='127.0.0.1', port=8080):
        """ A ZMQServer allowing remote access of a robot instance.

        The server used the REQ/REP zmq pattern. You should always first send a request and then read the answer.

        """
        AbstractServer.__init__(self, robot)

        c = zmq.Context()
        self.socket = c.socket(zmq.REP)
        self.socket.bind('tcp://{}:{}'.format(host, port))

        logger.info('Starting ZMQServer on tcp://%s:%s', host, port)

    def run(self):
        """ Run an infinite REQ/REP loop. """
        while True:
            req = self.socket.recv_json()

            try:
                answer = self.request_handler.handle_request(req)
                self.socket.send(json.dumps(answer, cls=MyJSONEncoder))

            except (AttributeError, TypeError) as e:
                self.socket.send_json({'error': e.message})

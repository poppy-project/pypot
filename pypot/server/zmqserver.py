import zmq

from pypot.server.server import AbstractServer, MyJSONEncoder

class ZMQServer(AbstractServer):
    def __init__(self, robot, host='127.0.0.1', port=8080):
        AbstractServer.__init__(self, robot)
    
        c = zmq.Context()
        self.socket = c.socket(zmq.REP)
        self.socket.bind('tcp://{}:{}'.format(host, port))

    def run(self):
        while True:
            req = self.socket.recv_json()

            try:
                answer = self.request_handler.handle_request(req)
                self.socket.send(json.dumps(answer, cls=MyJSONEncoder))
            
            except (AttributeError, TypeError) as e:
                self.socket.send_json({'error': e.message})


import zmq

import pypot.primitive

from operator import attrgetter

def attrsetter(item):
    def resolve_attr(obj, attr):
        for name in attr.split('.'):
            obj = getattr(obj, name)
        return obj

    def g(obj, value):
        var_path, _, var_name = item.rpartition('.')
        setattr(resolve_attr(obj, var_path), var_name, value)


class Server(pypot.primitive.Primitive):
    def __init__(self, addr='127.0.0.1', port=8888):
        c = zmq.Context()
        self.socket = c.socket(zmq.REP)
        self.socket.bind('tcp://{}:{}'.format(addr, port))

    def serve_forever(self):
        self.start()

    def run(self):
        while True:
            request = self.socket.recv_json()

            try:
                header = request['header']

                if header in ('GET', 'SET'):
                    obj = request['obj']
                    var_path = request['var_path']

                    if header == 'GET':
                        v = attrgetter(var_path)(obj)
                        self.socket.send_json(dict(ret_val='ok',
                                                   value=v))

                    else:
                        v = request['value']
                        attrsetter(var_path)(obj, value)
                        self.socket.send_json(dict(ret_val='ok'))

                elif header == 'CMD':
                    pass


            except (AttributeError, KeyError):
                logging.error('can not handle request: {}'.format(request))
                self.socket.send_json(dict(ret_val='ko'))
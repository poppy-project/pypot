import zmq
import logging

import pypot.primitive

from operator import attrgetter, methodcaller

def attrsetter(item):
    def resolve_attr(obj, attr):
        if not attr:
            return obj
        for name in attr.split('.'):
            obj = getattr(obj, name)
        return obj

    def g(obj, value):
        var_path, _, var_name = item.rpartition('.')
        setattr(resolve_attr(obj, var_path), var_name, value)

    return g


class Server(pypot.primitive.Primitive):
    def __init__(self, robot, addr='127.0.0.1', port=7777):
        pypot.primitive.Primitive.__init__(self, robot)
        
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

                obj = getattr(self.robot, request['obj'])

                if header in ('GET', 'SET'):
                    var_path = request['var_path']

                    if header == 'GET':
                        v = attrgetter(var_path)(obj)
                        self.socket.send_json(dict(succeed=True,
                                                   value=v))

                    else:
                        value = request['value']
                        attrsetter(var_path)(obj, value)
                        self.socket.send_json(dict(succeed=True))

                elif header == 'CMD':
                    f = request['cmd']
                    args = request['args'] if 'args' in request else ()
                    kwargs = request['kwargs'] if 'kwargs' in request else {}
                    methodcaller(f, *args, **kwargs)(obj)
        
                    self.socket.send_json(dict(succeed=True))


            except (AttributeError, KeyError) as e:
                logging.error(e)
                logging.error('can not handle request: {}'.format(request))
                self.socket.send_json(dict(succeed=False))
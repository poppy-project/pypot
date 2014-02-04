import json

import pypot.primitive

from pypot.server.request import BaseRequestHandler


# TODO: The server should spawn a new primitive for each client


class AbstractServer(pypot.primitive.Primitive):
    """ Abstract Server which mostly delegate the work to a request handler. """
    def __init__(self, robot, handler=BaseRequestHandler):
        pypot.primitive.Primitive.__init__(self, robot)

        self.request_handler = BaseRequestHandler(self.robot)


class MyJSONEncoder(json.JSONEncoder):
    """ JSONEncoder which tries to call a json property before using the enconding default function. """
    def default(self, obj):
        return obj.json if hasattr(obj, 'json') else json.JSONEncoder.default(self, obj)

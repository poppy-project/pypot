import json

import pypot.primitive

from pypot.server.request import BaseRequestHandler


# TODO: The server should spawn a new primitive for each client


class AbstractServer(pypot.primitive.Primitive):
    def __init__(self, robot, handler=BaseRequestHandler):
        pypot.primitive.Primitive.__init__(self, robot)
        
        self.request_handler = BaseRequestHandler(self.robot)



class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'json'):
            return obj.json
        else:
            return json.JSONEncoder.default(self, obj)
import bottle
import logging
import json

from .server import AbstractServer, MyJSONEncoder


logger = logging.getLogger(__name__)


class HTTPServer(AbstractServer):
    """ Bottle based HTTPServer used to remote access a robot.

        The server answers to the following requests:

        * GET /motor/list.json
        * GET /primitive/list.json
        * GET /motor/<name>/register.json (or GET /<name>/register.json)
        * GET /motor/<name>/<register> (or GET /<name>/<register>)
        * POST /motor/<name>/<register> (or POST /<name>/<register>)
        * POST /primitive/<prim_name>/call/<meth_name> (or GET /<prim_name>/call/<meth_name>)
        * POST /request.json

     """
    def __init__(self, robot, host='localhost', port=8080):
        AbstractServer.__init__(self, robot)

        self.host = host
        self.port = port

        self.app = bottle.Bottle()
        self.app.install(bottle.JSONPlugin(json_dumps=lambda s: json.dumps(s, cls=MyJSONEncoder)))

        @self.app.get('/motor/list.json')
        def get_motor_list():
            req = {
                'get': {
                    '': ['motors', ]
                }
            }

            return self.request_handler.handle_request(req)['get']['']

        @self.app.get('/primitive/list.json')
        def get_primitive_list():
            req = {
                'get': {
                    '': ['attached_primitives_name', ]
                }
            }
            return self.request_handler.handle_request(req)['get']['']

        @self.app.get('/<name>/register.json')
        @self.app.get('/motor/<name>/register.json')
        def get_motor_register(name):
            req = {
                'get': {
                    name: ['registers', ]
                }
            }
            return self.request_handler.handle_request(req)['get'][name]

        @self.app.get('/<name>/<register>')
        @self.app.get('/motor/<name>/<register>')
        def get_object_register(name, register):
            req = {
                'get': {
                    name: [register, ]
                }
            }

            return self.request_handler.handle_request(req)['get'][name]

        @self.app.post('/<name>/<register>')
        @self.app.post('/motor/<name>/<register>')
        def set_object_register(name, register):
            req = {
                'set': {
                    name: {register: bottle.request.json}
                }
            }

            return self.request_handler.handle_request(req)

        @self.app.post('/<prim_name>/call/<meth_name>')
        @self.app.post('/primitive/<prim_name>/call/<meth_name>')
        def call_prim_meth(prim_name, meth_name):
            req = {
                'call': {
                    prim_name: {meth_name: bottle.request.json}
                }
            }
            return self.request_handler.handle_request(req)['call'][prim_name]

        @self.app.post('/request.json')
        def request():
            return self.request_handler.handle_request(bottle.request.json)

        logger.info('Starting HTTPServer on http://%s:%s', host, port)

    def run(self):
        """ Start the bottle server, run forever. """
        bottle.run(self.app,
                   host=self.host, port=self.port,
                   quiet=True,
                   server='tornado')

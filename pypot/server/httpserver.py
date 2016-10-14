import json
import socket
import errno
import numpy
import bottle
from bottle import response

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

import logging

from .server import AbstractServer


logger = logging.getLogger(__name__)


class MyJSONEncoder(json.JSONEncoder):

    """ JSONEncoder which tries to call a json property before using the enconding default function. """

    def default(self, obj):
        if hasattr(obj, 'json'):
            return obj.json

        if isinstance(obj, numpy.ndarray):
            return list(obj)

        return json.JSONEncoder.default(self, obj)


class EnableCors(object):

    """Enable CORS (Cross-Origin Resource Sharing) headers"""
    name = 'enable_cors'
    api = 2

    def __init__(self, origin="*"):
        self.origin = origin

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = self.origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


class HTTPRobotServer(AbstractServer):

    """ Bottle based HTTPServer used to remote access a robot.

        Please refer to the REST API for an exhaustive list of the possible routes.

     """

    def __init__(self, robot, host='0.0.0.0', port='8080', cross_domain_origin='*', quiet=True):
        AbstractServer.__init__(self, robot, host, port)
        self.quiet = quiet
        self.app = bottle.Bottle()

        jd = lambda s: json.dumps(s, cls=MyJSONEncoder)
        self.app.install(bottle.JSONPlugin(json_dumps=jd))

        if(cross_domain_origin):
            self.app.install(EnableCors(cross_domain_origin))

        rr = self.restfull_robot

        @self.app.route("/", method=['OPTIONS'])
        @self.app.route("/<p:path>", method=['OPTIONS'])
        def options(p=""):
            return ""

        # Motors route
        @self.app.get('/')
        @self.app.get('/robot.json')
        def robot():
            out = {
                'motors': [],
                'primitives': []
            }
            for m in rr.get_motors_list('motors'):
                motor = {}
                for r in rr.get_motor_registers_list(m):
                    try:
                        motor[r] = rr.get_motor_register_value(m, r)
                    except AttributeError:
                        pass
                out['motors'].append(motor)

            running_primitives = rr.get_running_primitives_list()
            for prim in rr.get_primitives_list():
                primitve = {'primitive': prim,
                            'running': prim in running_primitives,
                            'properties': [],
                            'methods': rr.get_primitive_methods_list(prim)
                            }
                for prop in rr.get_primitive_properties_list(prim):
                    primitve['properties'].append({'property': prop, 'value': rr.get_primitive_property(prim, prop)})
                out['primitives'].append(primitve)

            return out

        @self.app.get('/motor/list.json')
        @self.app.get('/motor/<alias>/list.json')
        def get_motor_list(alias='motors'):
            return {
                alias: rr.get_motors_list(alias)
            }

        @self.app.get('/sensor/list.json')
        def get_sensor_list():
            return {
                'sensors': rr.get_sensors_list()
            }

        @self.app.get('/motor/alias/list.json')
        def get_motor_alias():
            return {
                'alias': rr.get_motors_alias()
            }

        @self.app.get('/motor/<motor_name>/register/list.json')
        @self.app.get('/sensor/<motor_name>/register/list.json')
        def get_motor_registers(motor_name):
            return {
                'registers': rr.get_motor_registers_list(motor_name)
            }

        @self.app.get('/motor/<motor_name>/register/<register_name>')
        @self.app.get('/sensor/<motor_name>/register/<register_name>')
        def get_register_value(motor_name, register_name):
            return {
                register_name: rr.get_motor_register_value(motor_name, register_name)
            }

        @self.app.post('/motor/<motor_name>/register/<register_name>/value.json')
        @self.app.post('/sensor/<motor_name>/register/<register_name>/value.json')
        def set_register_value(motor_name, register_name):
            rr.set_motor_register_value(motor_name, register_name,
                                        bottle.request.json)
            return {}

        # Sensors route

        # Primitives route
        @self.app.get('/primitive/list.json')
        def get_primitives_list():
            return {
                'primitives': rr.get_primitives_list()
            }

        @self.app.get('/primitive/running/list.json')
        def get_running_primitives_list():
            return {
                'running_primitives': rr.get_running_primitives_list()
            }

        @self.app.get('/primitive/<prim>/start.json')
        def start_primitive(prim):
            rr.start_primitive(prim)

        @self.app.get('/primitive/<prim>/stop.json')
        def stop_primitive(prim):
            rr.stop_primitive(prim)

        @self.app.get('/primitive/<prim>/pause.json')
        def pause_primitive(prim):
            rr.pause_primitive(prim)

        @self.app.get('/primitive/<prim>/resume.json')
        def resume_primitive(prim):
            rr.resume_primitive(prim)

        @self.app.get('/primitive/<prim>/property/list.json')
        def get_primitive_properties_list(prim):
            return {
                'property': rr.get_primitive_properties_list(prim)
            }

        @self.app.get('/primitive/<prim>/property/<prop>')
        def get_primitive_property(prim, prop):
            res = rr.get_primitive_property(prim, prop)
            return {
                '{}.{}'.format(prim, prop): res
            }

        @self.app.post('/primitive/<prim>/property/<prop>/value.json')
        def set_primitive_property(prim, prop):
            rr.set_primitive_property(prim, prop,
                                      bottle.request.json)

        @self.app.get('/primitive/<prim>/method/list.json')
        def get_primitive_methods_list(prim):
            return {
                'methods': rr.get_primitive_methods_list(self, prim)
            }

        @self.app.post('/primitive/<prim>/method/<meth>/args.json')
        def call_primitive_method(prim, meth):
            res = rr.call_primitive_method(prim, meth,
                                           bottle.request.json)
            return {
                '{}:{}'.format(prim, meth): res
            }

        @self.app.get('/motors/register/<register_name>')
        def get_motors_register_value(register_name):
            motors_list = rr.get_motors_list('motors')
            registers_motors = {}

            for motor_name in motors_list:
                registers_motors[motor_name] = {
                    register_name: rr.get_motor_register_value(motor_name, register_name)
                }

            return registers_motors

    def run(self, quiet=None):
        """ Start the tornado server, run forever.
            'quiet' and 'server' arguments are no longer used, they are keep only for backward compatibility.
        """

        try:
            loop = IOLoop()
            http_server = HTTPServer(WSGIContainer(self.app))
            http_server.listen(self.port)
            loop.start()

        except socket.error as serr:
            # Re raise the socket error if not "[Errno 98] Address already in use"
            if serr.errno != errno.EADDRINUSE:
                raise serr
            else:
                logger.warning("""The webserver port {} is already used.
The HttpRobotServer is maybe already run or another software use this port.""".format(self.port))

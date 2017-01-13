import json
import socket
import errno
import numpy

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler
from tornado.web import Application

from bottle import response

import json
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
            response.set_header('Access-Control-Allow-Origin', self.origin)
            response.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            response.set_header('Access-Control-Allow-Headers', 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token')

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


class CacheBuster(object):
    """Add response headers to disable cache"""

    name = 'cache_buster'
    api = 2

    def apply(self, fn, context):
        def _ext(*args, **kwargs):
            response.set_header('Cache-control', 'no-store')
            return fn(*args, **kwargs)

        return _ext


class PoppyRequestHandler(RequestHandler):
    """Custom request handler.

    Automatically sets CORS and cache headers, and manages
    every OPTIONS request."""

    def set_default_headers(self):
        self.set_header('Cache-control', 'no-store')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')

    def options(self):
        self.set_status(204)

    def write_json(self, obj):
        self.write(json.dumps(obj))

class IndexHandler(PoppyRequestHandler):
    def get(self):
        out = {
            'motors': [],
            'primitives': []
        }
        for m in self.restful_robot.get_motors_list('motors'):
            motor = {}
            for r in self.restful_robot.get_motor_registers_list(m):
                try:
                    motor[r] = self.restful_robot.get_motor_register_value(m, r)
                except AttributeError:
                    pass
            out['motors'].append(motor)

        running_primitives = self.restful_robot.get_running_primitives_list()
        for prim in self.restful_robot.get_primitives_list():
            primitve = {
                'primitive': prim,
                'running': prim in running_primitives,
                'properties': [],
                # XXX pas de self en param ?
                'methods': self.restful_robot.get_primitive_methods_list(prim)
            }
            for prop in self.restful_robot.get_primitive_properties_list(prim):
                primitve['properties'].append({
                    'property': prop,
                    'value': self.restful_robot.get_primitive_property(prim, prop)
                })
            out['primitives'].append(primitve)

        self.write_json(out)

# @self.app.get('/motor/list.json')
# @self.app.get('/motor/<alias>/list.json')
class MotorsListHandler(PoppyRequestHandler):
    def get(self, alias='motors'):
        self.write_json({
            'alias': self.restful_robot.get_motors_list(alias)
        })

# @self.app.get('/sensor/list.json')
class SensorsListHandler(PoppyRequestHandler):
    def get(self):
        self.write_json({
            'sensors': self.restful_robot.get_sensors_list()
        })

# @self.app.get('/motor/alias/list.json')
class MotorsAliasesListHandler(PoppyRequestHandler):
    def get(self):
        self.write_json({
            'alias': self.restful_robot.get_motors_alias()
        })

# @self.app.get('/motor/<motor_name>/register/list.json')
# @self.app.get('/sensor/<motor_name>/register/list.json')
class MotorRegistersListHandler(PoppyRequestHandler):
    def get(self, motor_name):
        self.write_json({
            'registers': self.restful_robot.get_motor_registers_list(motor_name)
        })

# @self.app.get('/motor/<motor_name>/register/<register_name>')
# @self.app.get('/sensor/<motor_name>/register/<register_name>')
class MotorRegisterHandler(PoppyRequestHandler):
    def get(self, motor_name, register_name):
        self.write_json({
            register_name: self.restful_robot.get_motor_register_value(motor_name, register_name)
        })

# @self.app.post('/motor/<motor_name>/register/<register_name>/value.json')
# @self.app.post('/sensor/<motor_name>/register/<register_name>/value.json')
class UpdateMotorRegisterHandler(PoppyRequestHandler):
    def post(self, motor_name, register_name):
        pass
        # self.restful_robot.set_motor_register_value(
        #     motor_name, register_name, bottle.request.json)
        # self.write_json({})

# @self.app.get('/primitive/list.json')
class PrimitivesListHandler(PoppyRequestHandler):
    def get(self):
        self.write_json({
            'primitives': self.restful_robot.get_primitives_list()
        })

# @self.app.get('/primitive/running/list.json')
class RunningPrimitivesListHandler(PoppyRequestHandler):
    def get(self):
        self.write_json({
            'running_primitives': self.restful_robot.get_running_primitives_list()
        })

# @self.app.get('/primitive/<prim>/start.json')
class StartPrimitiveHandler(PoppyRequestHandler):
    def get(self, primitive_name):
        self.restful_robot.start_primitive(primitive_name)

# @self.app.get('/primitive/<prim>/stop.json')
class StopPrimitiveHandler(PoppyRequestHandler):
    def get(self, primitive_name):
        self.restful_robot.stop_primitive(primitive_name)

# @self.app.get('/primitive/<prim>/pause.json')
class PausePrimitiveHandler(PoppyRequestHandler):
    def get(self, primitive_name):
        self.restful_robot.pause_primitive(primitive_name)

# @self.app.get('/primitive/<prim>/resume.json')
class ResumePrimitiveHandler(PoppyRequestHandler):
    def get(self, primitive_name):
        self.restful_robot.resume_primitive(primitive_name)

# @self.app.get('/primitive/<prim>/property/list.json')
class PrimitivePropertiesListHandler(PoppyRequestHandler):
    def get(self, primitive_name):
        self.write_json({
            'property': self.restful_robot.get_primitive_properties_list(primitive_name)
        })

# @self.app.get('/primitive/<prim>/property/<prop>')
class PrimitivePropertyHandler(PoppyRequestHandler):
    def get(self, primitive_name, prop):
        response = self.restful_robot.get_primitive_property(primitive_name, prop)
        self.write_json({
            '{}.{}'.format(primitive_name, prop): response
        })

# ????
# @self.app.post('/primitive/<prim>/property/<prop>/value.json')
# def set_primitive_property(prim, prop):
#     rr.set_primitive_property(prim, prop,
#                               bottle.request.json)
class SetPrimitivePropertyHandler(PoppyRequestHandler):
    def post(self, primitive_name, prop):
        pass
        # data = self.get_argument('data', {})

        # self.restful_robot.set_primitive_property(
        #     primitive_name, prop, bottle.request.json)

# @self.app.get('/primitive/<prim>/method/list.json')
class ListPrimitiveMethodsHandler(PoppyRequestHandler):
    def get(self, primitive_name):
        self.write_json({
            'methods': self.restful_robot.get_primitive_methods_list(self, primitive_name)
        })

# @self.app.post('/primitive/<prim>/method/<meth>/args.json')
# def call_primitive_method(prim, meth):
#     res = rr.call_primitive_method(prim, meth,
#                                    bottle.request.json)
#     return {
#         '{}:{}'.format(prim, meth): res
#     }
class CallPrimitiveMethodHandler(PoppyRequestHandler):
    def post(self, primitive_name, method_name):
        # @TODO remove bottle
        # response = rr.call_primitive_method(primitive_name, method_name, bottle.request.json)
        # self.write_json({
        #     '{}:{}'.format(primitive_name, method_name): response
        # })

# @self.app.get('/motors/register/<register_name>')
class MotorsRegistersHandler(PoppyRequestHandler):
    def get(self, register_name):
        motors_list = self.restful_robot.get_motors_list('motors')
        registers_motors = {}

        for motor_name in motors_list:
            registers_motors[motor_name] = {
                register_name: self.restful_robot.get_motor_register_value(
                    motor_name, register_name)
            }

        self.write_json(registers_motors)


class HTTPRobotServer(AbstractServer):

    """Refer to the REST API for an exhaustive list of the possible routes."""

    def __init__(self, robot, host='0.0.0.0', port='8080', cross_domain_origin='*', **kwargs):
        AbstractServer.__init__(self, robot, host, port)

        # jd = lambda s: json.dumps(s, cls=MyJSONEncoder)

    def make_app(self):
        PoppyRequestHandler.restful_robot = self.restful_robot
        return Application([
            (r'/(robots\.json)?', IndexHandler),
            (r'/motor/(?P<alias>[a-zA-Z0-9_]+)/?list\.json', MotorsListHandler),
            (r'/sensor/list\.json', SensorsListHandler),
            (r'/motor/alias/list\.json', MotorsAliasesListHandler),
            (r'/motor/(?P<motor_name>[a-zA-Z0-9_]+)/register/list\.json', MotorRegistersListHandler),
            (r'/(motor|sensor)/(?P<motor_name>[a-zA-Z0-9_]+)/register/(?P<register_name>[a-zA-Z0-9_]+)/list/.json', MotorRegistersListHandler),
            (r'/(motor|sensor)/(?P<motor_name>[a-zA-Z0-9_]+)/register/(?P<register_name>[a-zA-Z0-9_]+)', MotorRegisterHandler),
            (r'/(motor|sensor)/(?P<motor_name>[a-zA-Z0-9_]+)/register/(?P<register_name>[a-zA-Z0-9_]+)/value\.json', UpdateMotorRegisterHandler),
            (r'/primitive/list\.json', PrimitivesListHandler),
            (r'/primitive/running/list\.json', RunningPrimitivesListHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/start\.json', StartPrimitiveHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/stop\.json', StopPrimitiveHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/pause\.json', PausePrimitiveHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/resume\.json', ResumePrimitiveHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/property/list\.json', PrimitivePropertiesListHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/property/(?P<prop>[a-zA-Z0-9_]+)', PrimitivePropertyHandler),
            # @TODO fix next route
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/property/(?P<prop>[a-zA-Z0-9_]+)/value\.json', SetPrimitivePropertyHandler),
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/method/list\.json', ListPrimitiveMethodsHandler),
            # @TODO fix next route
            (r'/primitive/(?P<primitive_name>[a-zA-Z0-9_]+)/method/(?P<method_name>[a-zA-Z0-9_]+)/args\.json', CallPrimitiveMethodHandler),
            (r'/motors/register/(?P<register_name>[a-zA-Z0-9_]+)', MotorsRegistersHandler),
        ])

    def run(self, **kwargs):
        """ Start the tornado server, run forever"""

        try:
            loop = IOLoop()
            app = self.make_app()
            app.listen(self.port)
            loop.start()

        except socket.error as serr:
            # Re raise the socket error if not "[Errno 98] Address already in use"
            if serr.errno != errno.EADDRINUSE:
                raise serr
            else:
                logger.warning('The webserver port {} is already used. May be the HttpRobotServer is already running or another software is using this port.'.format(self.port))

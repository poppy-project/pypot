import json
import numpy
import bottle
import logging

from .server import AbstractServer


logger = logging.getLogger(__name__)


class MyJSONEncoder(json.JSONEncoder):
    """ JSONEncoder which tries to call a json property before using the enconding default function. """
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return list(obj)

        return json.JSONEncoder.default(self, obj)


class HTTPRobotServer(AbstractServer):
    """ Bottle based HTTPServer used to remote access a robot.

        Please refer to the REST API for an exhaustive list of the possible routes.

     """
    def __init__(self, robot, host, port):
        AbstractServer.__init__(self, robot, host, port)

        self.app = bottle.Bottle()

        jd = lambda s: json.dumps(s, cls=MyJSONEncoder)
        self.app.install(bottle.JSONPlugin(json_dumps=jd))

        rr = self.restfull_robot

        # Motors route

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
        def get_primitives_list(self):
            return {
                'primitives': rr.get_primitives_list()
            }

        @self.app.get('/primitive/running/list.json')
        def get_running_primitives_list(self):
            return {
                'running_primitives': rr.get_running_primitives_list()
            }

        @self.app.get('/primitive/<prim>/start.json')
        def start_primitive(self, prim):
            rr.start_primitive(prim)

        @self.app.get('/primitive/<prim>/stop.json')
        def stop_primitive(self, prim):
            rr.stop_primitive(prim)

        @self.app.get('/primitive/<prim>/pause.json')
        def pause_primitive(self, prim):
            rr.pause_primitive(prim)

        @self.app.get('/primitive/<prim>/resume.json')
        def resume_primitive(self, prim):
            rr.resume_primitive(prim)

        @self.app.get('/primitive/<prim>/property/list.json')
        def get_primitive_properties_list(self, prim):
            return {
                'property': rr.get_primitive_properties_list(prim)
            }

        @self.app.get('/primitive/<prim>/property/<prop>')
        def get_primitive_property(self, prim, prop):
            res = rr.get_primitive_property(prim, prop)
            return {
                '{}.{}'.format(prim, prop): res
            }

        @self.app.post('/primitive/<prim>/property/<prop>/value.json')
        def set_primitive_property(self, prim, prop):
            rr.set_primitive_property(prim, prop,
                                      bottle.request.json)

        @self.app.get('/primitive/<prim>/method/list.json')
        def get_primitive_methods_list(self, prim):
            return {
                'methods': rr.get_primitive_methods_list(self, prim)
            }

        @self.app.post('/primitive/<prim>/method/<meth>/args.json')
        def call_primitive_method(self, prim, meth):
            res = rr.call_primitive_method(prim, meth,
                                           bottle.request.json)
            return {
                '{}:{}'.format(prim, meth): res
            }

    def run(self, quiet=False, server='tornado'):
        """ Start the bottle server, run forever. """
        bottle.run(self.app,
                   host=self.host, port=self.port,
                   quiet=quiet,
                   server=server)

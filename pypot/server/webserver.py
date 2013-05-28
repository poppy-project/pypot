import itertools
import bottle
import json

from pypot.server.server import AbstractServer, MyJSONEncoder

class HTTPServer(AbstractServer):
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
                    '': ['motors',]
                }
            }
            return self.request_handler.handle_request(req)['get']['']
        
        @self.app.get('/motor/<name>/register.json')
        def get_motor_register(name):
            req = {
                'get': {
                    name: ['registers',]
                }
            }
            return self.request_handler.handle_request(req)['get'][name]

        @self.app.get('/motor/<name>/<register>')
        def get_motor_register(name, register):
            req = {
                'get': {
                    name: [register, ]
                }
            }

            return self.request_handler.handle_request(req)['get'][name]
                
        #@self.app.post('/motor/<name>/<register>')
        #def set_motor_register(name, register):
        #    setattr(getattr(self.robot, name), register, bottle.request.json)
        
        @self.app.post('/motors/getvalues.json')
        def get_motors_registers():
            return self.request_handler.handle_request({'get': bottle.request.json})
            
        @self.app.get('/motor_position')
        def pos():
            req = {'get': dict(zip(self.robot.motors_name, itertools.repeat(['present_position', ])))}
            return self.request_handler.handle_request(req)
        
        @self.app.get('/motor_temperature')
        def temp():
            req = {'get': dict(zip(self.robot.motors_name, itertools.repeat(['present_temperature', ])))}
            return self.request_handler.handle_request(req)
        
        @self.app.get('/sensor')
        def sensor():
            req = {'get': {
                        'imu': ['acc.x', 'acc.y', 'acc.z',
                                'tilt.x', 'tilt.y', 'tilt.z',
                                'gyro.x', 'gyro.y', 'gyro.z'],
                        'left_foot': ['pressor_values', ],
                        'right_foot': ['pressor_values', ],
                        }
                    }
            return self.request_handler.handle_request(req)
        
    
        @self.app.route('/static/:filename#.*#')
        def send_static(filename):
            return bottle.static_file(filename, root='./static/')
                
        @self.app.route('/')
        def index():
            return bottle.static_file('index.html', root='./static/')
    
        # @self.app.post('/motors/setvalues.json')
        # def set_motors_registers():
        #     for name, registers in bottle.request.json.iteritems():
        #         m = getattr(self.robot, name)
                
        #         for r, v in registers.iteritems():
        #             setattr(m, r, v)
    
        # @self.app.get('/primitive/list.json')
        # def get_primitive_list():
        #     return json.dumps(self.robot.primitives)
    
        # @self.app.get('/primitive/<name>/call/<action>')
        # @self.app.post('/primitive/<name>/call/<action>')
        # def call_primitive_method(name, action):
        #     f = attrgetter('{}.{}'.format(name, action))
            
        #     r = f(self.robot)(bottle.request.json) if bottle.request.json else f(self.robot)()
        #     if r:
        #         return json.dumps(r)
        
        # @self.app.get('/primitive/<name>/<varpath>')
        # def get_primitive_variable(name, varpath):
        #     f = attrgetter('{}.{}'.format(name, varpath))
        #     return json.dumps(f(self.robot))
        
        # @self.app.post('/primitive/<name>/<varpath>')
        # def set_primitive_variable(name, varpath, value):
        #     f = attrsetter('{}.{}'.format(name, varpath))
        #     f(self.robot, bottle.request.json)
    
    
    def run(self):
        bottle.run(self.app,
                   host=self.host, port=self.port,
                   quiet=True,
                   server='tornado')


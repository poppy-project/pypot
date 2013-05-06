import bottle
import json

from operator import attrgetter


import pypot.primitive

from pypot.utils import attrsetter

class HTTPServer(pypot.primitive.Primitive):
    def __init__(self, robot):
        pypot.primitive.Primitive.__init__(self, robot)
    
        self.app = bottle.Bottle()
    
        @self.app.get('/motor/list.json')
        def get_motor_list():
            return json.dumps([m.name for m in self.robot.motors])

        @self.app.get('/motor/<name>/register.json')
        def get_motor_register(name):
            return json.dumps(getattr(self.robot, name).registers)
        
        @self.app.get('/motor/<name>/<register>')
        def get_motor_register(name, register):
            return json.dumps(attrgetter(register)(getattr(self.robot, name)))
        
        @self.app.post('/motor/<name>/<register>')
        def set_motor_register(name, register):
            setattr(getattr(self.robot, name), register, bottle.request.json)
        
        @self.app.post('/motors/getvalues.json')
        def get_motors_registers():
            values = {}
            for name, registers in bottle.request.json.iteritems():
                values[name] = [attrgetter(r)(getattr(self.robot, name)) for r in registers]
            
            return values
    
        @self.app.post('/motors/setvalues.json')
        def set_motors_registers():
            for name, registers in bottle.request.json.iteritems():
                m = getattr(self.robot, name)
                
                for r, v in registers.iteritems():
                    setattr(m, r, v)    
   
        @self.app.get('/primitive/list.json')
        def get_primitive_list():
            return json.dumps(self.robot.primitives_name)
    
        @self.app.get('/primitive/<name>/call/<action>')
        @self.app.post('/primitive/<name>/call/<action>')
        def call_primitive_method(name, action):
            f = attrgetter('{}.{}'.format(name, action))
    
            r = f(self.robot)(bottle.request.json) if bottle.request.json else f(self.robot)()
            if r:
                return json.dumps(r)

        @self.app.get('/primitive/<name>/<varpath>')
        def get_primitive_variable(name, varpath):
            f = attrgetter('{}.{}'.format(name, varpath))
            return json.dumps(f(self.robot))

        @self.app.post('/primitive/<name>/<varpath>')
        def set_primitive_variable(name, varpath, value):
            f = attrsetter('{}.{}'.format(name, varpath))
            f(self.robot, bottle.request.json)

    
    def run(self):
        bottle.run(self.app, host='localhost', port=8080, quiet=False)


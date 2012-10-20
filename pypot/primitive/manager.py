import time
import numpy
import threading

from pypot.utils import camel_case_to_lower_case

class PrimitiveManager(threading.Thread):
    def __init__(self, robot, filter=numpy.mean):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.primitives = {}
        self.filter = filter
        
        self.frequency = 50
        self.robot = robot
    

    def add(self, primitive_cls, *args, **kwargs):
        if 'name' in kwargs:
            name = kwargs['name']
        else:
            name = camel_case_to_lower_case(primitive_cls.__name__)
        
        if name in self.primitives:
            raise ValueError('A primitive with the name {} already exists !'.format(name))

        self.primitives[name] = primitive_cls(*args)
    
        class Holder:
            p = property(lambda x: self.primitives[name])
    
        setattr(self, name, Holder().p)
    
    def remove(self, name):
        delattr(self, name)
        del self.primitives[name]

    
    def run(self):
        while True:
            changes = {}
            
            for p in self.primitives.values():
                dm = p.get_modified_values()

                for m, d in dm.iteritems():
                    if m not in changes:
                        changes[m] = {}
                    
                    for k, v in d.iteritems():
                        if k not in changes[m]:
                            changes[m][k] = []
        
                        changes[m][k].append(v)
    
            for motor, motor_changes in changes.iteritems():
                for register, values in motor_changes.iteritems():
                    filtred_value = self.filter(values)
                    
                    m = getattr(self.robot, motor)
                    setattr(m, register, filtred_value)
                        
            time.sleep(1.0 / self.frequency)





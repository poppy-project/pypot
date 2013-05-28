import json

from collections import defaultdict


from pypot.utils import attrgetter, attrsetter


class BaseRequestHandler(object):
    def __init__(self, robot):
        self.robot = robot

    def handle_request(self, request):
        answer = {}
        
        for meth in filter(lambda meth: meth in request, ('get', 'set', 'call')):
            f = getattr(self, 'handle_{}'.format(meth))
            answer[meth] = f(request[meth])

        return answer

    def handle_get(self, request):
        answer = defaultdict(dict)
        
        for obj_name, paths in request.iteritems():
            obj = getattr(self.robot, obj_name) if obj_name else self.robot
        
            for var_path in paths:
                answer[obj_name][var_path] = attrgetter(var_path)(obj)
        
        return answer

    def handle_set(self, request):
        for obj_name, value_pairs in request.iteritems():
            obj = getattr(self.robot, obj_name)
        
            for var_path, value in value_pairs.iteritems():
                attrsetter(var_path)(obj, value)

    def handle_call(self, request):
        answer = defaultdict(dict)
        
        for obj_name, meth_pairs in request.iteritems():
            obj = getattr(self.robot, obj_name)
            
            for meth, args in meth_pairs.iteritems():
                f = attrgetter(meth)(obj)
                answer[obj_name][meth] = f(args) if args else f()

        return answer

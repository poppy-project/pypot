import logging

from collections import defaultdict

from ..utils import attrgetter, attrsetter


logger = logging.getLogger(__name__)


class BaseRequestHandler(object):
    """ JSON request (get, set or call) handler. """

    def __init__(self, robot):
        self.robot = robot

    def handle_request(self, request):
        """ Handles a JSON request from the client.

            The request can contain at the same time a get, a set and a call request. Each of these requests can retrieve (resp. affect and call) multiple values at the same time, so for instance you can get the position, speed, load and temperature of multiple motors and get the pressure value of a sensor in the same request.

            The request are constructed as follows::

                {
                    'get': { ... },
                    'set': { ... },
                    'call': { ... }
                }

            .. note:: It is not mandatory to give a get, a set and a call request, you can build a request with only a get field.

            Each field of the request will be detailed in their respective handler.

            """
        answer = {}

        for meth in [meth for meth in ('get', 'set', 'call') if meth in request]:
            f = getattr(self, 'handle_{}'.format(meth))
            answer[meth] = f(request[meth])

        logger.debug('Handling request %s with answer %s', request, answer)

        return answer

    def handle_get(self, request):
        """ Handles the get field of a request.

            The get field is constructed as follows::

                {
                    'get': {
                        'obj_name_1': ('var_path_1', 'var_path_2', ...),
                        'obj_name_2': ('var_path_1', 'var_path_2', ...),
                        # ...
                        }
                    }

            For each couple obj_name_1, var_path_1, the handler will get the value corresponding to self.robot.obj_name_1.var_path_1: i.e. if we want to get the present_position and present_speed of the motor named l_knee_y we would use::

                {
                    'get': {
                        'l_knee_y': ('present_position', 'present_speed'),
                        }
                    }

            .. note:: The var_path could be complete path, e.g. "skeleton.left_foot.position.x".

            """
        answer = defaultdict(dict)

        for obj_name, paths in request.iteritems():
            obj = getattr(self.robot, obj_name) if obj_name else self.robot

            for var_path in paths:
                answer[obj_name][var_path] = attrgetter(var_path)(obj)

        return answer

    def handle_set(self, request):
        """ Handles the set field of a request.

            The set field is constructed as follows::

                {
                    'set': {
                        'obj_name_1': {'var_path_1': value,
                                        'var_path_2': value,
                                        # ...
                                        },
                        'obj_name_2': {'var_path_1': value,
                                        'var_path_2': value,
                                       # ...
                                        },
                        # ...
                    }
                }

            For each triple obj_name_1, var_path_1, value the handler will set the corresponding value to self.robot.obj_name_1.var_path_1: i.e. if we want to set the goal_position and goal_speed of the motor named l_knee_y to resp. 0 and 100 we would use::

                {
                    'set': {
                        'l_knee_y': {'goal_position': 0, 'present_speed': 100},
                        }
                    }

            .. note:: The var_path could be complete path, e.g. "skeleton.left_foot.position.x".

            """
        for obj_name, value_pairs in request.iteritems():
            obj = getattr(self.robot, obj_name)

            for var_path, value in value_pairs.iteritems():
                attrsetter(var_path)(obj, value)

    def handle_call(self, request):
        """ Handles the call field of a request.

            The call field is constructed as follows::

                'call': {
                    'obj_name_1': {'meth_path_1': (arg1, arg2, ...),
                                    'meth_path_2': (arg1, arg2, ...),
                                    ...
                                    },

                    'obj_name_2': {'meth_path_1': (arg1, arg2, ...),
                                    'meth_path_2': (arg1, arg2, ...),
                                    ...
                                    },
                        ...
                        }

            For each tuple obj_name_1, meth_path_1 and args  the handler will call the corresponding method of the object with the args: i.e. if we want to call the switch_mode method of a primitive named 'balance' to switch to the third mode we would use::

                'call': {
                    'balance': {'switch_mode': (3, )}
                    }

            .. note:: To call a method without argument juste use an empty list as args::

                'call': {'balance': {'start': ()}}

            """
        answer = defaultdict(dict)

        for obj_name, meth_pairs in request.iteritems():
            obj = getattr(self.robot, obj_name)

            for meth, args in meth_pairs.iteritems():
                f = attrgetter(meth)(obj)
                answer[obj_name][meth] = f(*args) if args else f()

        return answer

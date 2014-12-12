from operator import attrgetter


class RESTRobot(object):
    """ REST API for a Robot.

    Through the REST API you can currently access:
        * the motors list (and the aliases)
        * the registers list for a specific motor
        * read/write a value from/to a register of a specific motor

        * the sensors list

        * the primitives list (and the active)
        * start/stop primitives

    """
    def __init__(self, robot):
        self.robot = robot

    # Access motor related values

    def get_motors_list(self, alias='motors'):
        return [m.name for m in getattr(self.robot, alias)]

    def get_registers_list(self, motor):
        return self.get_register_value(motor, 'registers')

    def get_register_value(self, motor, register):
        return attrgetter('{}.{}'.format(motor, register))(self.robot)

    def set_register_value(self, motor, register, value):
        m = getattr(self.robot, motor)
        setattr(m, register, value)

    def get_motors_alias(self):
        return self.robot.alias

    # Access sensor related values

    def get_sensors_list(self):
        return [s.name for s in self.robot.sensors]

    # Access primitive related values

    def get_primitives_list(self):
        return [p.name for p in self.robot.primitives]

    def get_running_primitives_list(self):
        return [p.name for p in self.robot.active_primitives]

    def start_primitive(self, primitive):
        self._call_primitive_method(primitive, 'start')

    def stop_primitive(self, primitive):
        self._call_primitive_method(primitive, 'stop')

    def pause_primitive(self, primitive):
        self._call_primitive_method(primitive, 'pause')

    def resume_primitive(self, primitive):
        self._call_primitive_method(primitive, 'resume')

    def get_primitive_properties_list(self, primitive):
        return getattr(self.robot, primitive).properties

    def get_primitive_property(self, primitive, property):
        return attrgetter('{}.{}'.format(primitive, property))(self.robot)

    def set_primitive_property(self, primitive, property, value):
        m = getattr(self.robot, primitive)
        setattr(m, property, value)

    def get_primitive_methods_list(self, primitive):
        return getattr(self.robot, primitive).methods

    def call_primitive_method(self, primitive, method, kwargs):
        self._call_primitive_method(self, primitive, method, **kwargs)

    def _call_primitive_method(self, primitive, method_name, *args, **kwargs):
        p = getattr(self.robot, primitive)
        f = getattr(p, method_name)
        return f(*args, **kwargs)

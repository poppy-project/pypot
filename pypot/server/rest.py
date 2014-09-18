from operator import attrgetter


class RESTRobot(object):
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
        return [m.name for m in self.robot.sensors]

from operator import attrgetter


class RESTRobot(object):
    """ REST API for a Robot.

    Through the REST API you can currently access:
        * the motors list (and the aliases)
        * the registers list for a specific motor
        * read/write a value from/to a register of a specific motor

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

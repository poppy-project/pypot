import os

from operator import attrgetter
from pypot.primitive.move import MovePlayer, MoveRecorder, Move
from pypot.primitive.utils import Cosinus, Sinus, LoopPrimitive, numpy


class RESTRobot(object):

    """ REST API for a Robot.

    Through the REST API you can currently access:
        * the motors list (and the aliases)
        * the registers list for a specific motor
        * read/write a value from/to a register of a specific motor

        * the sensors list
        * the registers list for a specific motor
        * read/write a value from/to a register of a specific motor

        * the primitives list (and the active)
        * start/stop primitives
    """

    def __init__(self, robot):
        self.robot = robot

    # Access motor related values

    def get_motors_list(self, alias='motors'):
        return [m.name for m in getattr(self.robot, alias)]

    def get_motor_registers_list(self, motor):
        return self._get_register_value(motor, 'registers')

    def get_motor_register_value(self, motor, register):
        return self._get_register_value(motor, register)

    def set_motor_register_value(self, motor, register, value):
        self._set_register_value(motor, register, value)

    def get_motors_alias(self):
        return self.robot.alias

    def set_goto_position_for_motor(self, motor, position, duration):
        m = getattr(self.robot, motor)
        m.goto_position(position, duration, wait=False)

    # Access sensor related values

    def get_sensors_list(self):
        return [s.name for s in self.robot.sensors]

    def get_sensors_registers_list(self, sensor):
        return self._get_register_value(sensor, 'registers')

    def get_sensor_register_value(self, sensor, register):
        return self._get_register_value(sensor, register)

    def set_sensor_register_value(self, sensor, register, value):
        return self._set_register_value(sensor, register, value)

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
        return self._get_register_value(primitive, property)

    def set_primitive_property(self, primitive, property, value):
        self._set_register_value(primitive, property, value)

    def get_primitive_methods_list(self, primitive):
        return getattr(self.robot, primitive).methods

    def call_primitive_method(self, primitive, method, kwargs):
        self._call_primitive_method(primitive, method, **kwargs)

    def _set_register_value(self, object, register, value):
        o = getattr(self.robot, object)
        setattr(o, register, value)

    def _get_register_value(self, object, register):
        return attrgetter('{}.{}'.format(object, register))(self.robot)

    def _call_primitive_method(self, primitive, method_name, *args, **kwargs):
        p = getattr(self.robot, primitive)
        f = getattr(p, method_name)
        return f(*args, **kwargs)

    def start_move_recorder(self, move_name, motors_name):
        if not hasattr(self.robot, '_{}_recorder'.format(move_name)):
            motors = [getattr(self.robot, m) for m in motors_name]
            recorder = MoveRecorder(self.robot, 50, motors)
            self.robot.attach_primitive(recorder, '_{}_recorder'.format(move_name))
            recorder.start()
        else:
            recorder = getattr(self.robot, '_{}_recorder'.format(move_name))
            recorder.start()

    def stop_move_recorder(self, move_name):
        """Allow more easily than stop_primitive() to save in a filename the recorcded move"""
        recorder = getattr(self.robot, '_{}_recorder'.format(move_name))
        recorder.stop()
        with open('{}.record'.format(move_name), 'w') as f:
            recorder.move.save(f)

    def start_move_player(self, move_name, speed=1.0):
        """Move player need to have a move file
        <move_name.record> in the working directory to play it"""
        if not hasattr(self.robot, '_{}_player'.format(move_name)):
            with open('{}.record'.format(move_name)) as f:
                loaded_move = Move.load(f)
            player = MovePlayer(self.robot, loaded_move)
            self.robot.attach_primitive(player, '_{}_player'.format(move_name))
        else:
            player = getattr(self.robot, '_{}_player'.format(move_name))
        player.speed = speed
        player.start()
        player.wait_to_stop()

    def get_available_record_list(self):
        """Get list of json recorded movement files"""
        return [f.split('.record')[0] for f in os.listdir('.') if f.endswith('.record')]

    def remove_move_record(self, move_name):
        """Remove the json recorded movement file"""
        return os.remove('{}.record'.format(move_name))

        # TO_CHECK
        # def __modify_names__(move_name, modify=None):
        #     if modify == 'player':
        #         return '_{}_player'.format(move_name)
        #     elif modify == 'recorder':
        #         return '_{}_recorder'.format(move_name)
        #     elif modify == 'save':
        #         return '{}.record'.format(move_name)
        #     else:
        #         raise NameError()
        #         raise NameError()

    def __find_words__(instring, words, prefix=''):
        """ Quick and dirty snippet to split string without space
            to a list of known words.
            Used to pass over a bug of Snap!"""
        if not instring:
            return []

        if (not prefix) and (instring in words):
            return [instring]
        prefix, suffix = prefix + instring[0], instring[1:]
        solutions = []
        # Case 1: prefix in solution
        if prefix in words:
            try:
                solutions.append([prefix] + __find_words__(suffix, words, ''))
            except ValueError:
                pass
        # Case 2: prefix not in solution
        try:
            solutions.append(__find_words__(suffix, words, prefix))
        except ValueError:
            pass
        if solutions:
            return sorted(solutions,
                          key=lambda solution: [len(word) for word in solution],
                          reverse=True)[0]
        else:
            return instring

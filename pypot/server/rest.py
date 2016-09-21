import os

from operator import attrgetter

from pypot.robot.motor import Motor
from pypot.robot.sensor import Sensor

from pypot.primitive.move import MovePlayer, MoveRecorder, Move


class RESTRobot(object):
    """ Bridge class to expose a REST API for a Robot.

    Through the REST API you can currently access:
        * the devices (either motor or sensor) list (and the groups)
        * the registers list for a specific device
        * read/write a value from/to a register of a specific device
        * the primitives list (and their status)
        * call methods of a primitive (start, stop, ...)
        * get/set properties of a primitive

    """
    def __init__(self, robot):
        self.robot = robot

    # Access groups related values
    def get_devices_groups(self):
        """ Returns the names of the groups of devices. """
        return self.robot.groups + ['motors', 'sensors']

    def get_devices_list(self, group):
        """ Returns the names of the devices of a group. """
        return [d.name for d in getattr(self.robot, group)]

    # Access device related values
    def get_device_registers_list(self, device):
        """ Returns the names of the registers of a device. """
        registers = list(self._get_register_value(device, 'registers'))
        registers.remove('registers')
        return registers

    def get_device_register_value(self, device, register):
        """ Returns the register value of a device. """
        return self._get_register_value(device, register)

    def set_device_register_value(self, device, register, value):
        """ Sets a new value of a register of a device. """
        self._set_register_value(device, register, value)

    def get_device_type(self, device_name):
        """ Returns the device type (motor, sensor or unknown). """
        device = getattr(self.robot, device_name)

        device_types = {
            Motor: 'motor',
            Sensor: 'sensor'
        }

        for cls, name in device_types.items():
            if isinstance(device, cls):
                return name
        return 'unknown'

    # Motor specifics
    def set_goto_position_for_motor(self, motor, position, duration):
        """ Triggers a goto position for a motor. """
        m = getattr(self.robot, motor)
        m.goto_position(position, duration, wait=False)

    # Access primitive related values
    def get_primitives_list(self, by_status=None):
        """ Returns the list of primitives.

            They can be filtred by status (running, paused, stopped).

        """
        return [p.name for p in self.robot.primitives
                if by_status is None or p.status == by_status]

    def start_primitive(self, primitive):
        """ Starts a primitive. """
        self._call_primitive_method(primitive, 'start')

    def stop_primitive(self, primitive):
        """ Stops a primitive. """
        self._call_primitive_method(primitive, 'stop')

    def pause_primitive(self, primitive):
        """ Pauses a primitive. """
        self._call_primitive_method(primitive, 'pause')

    def resume_primitive(self, primitive):
        """ Resumes a primitive. """
        self._call_primitive_method(primitive, 'resume')

    def get_primitive_properties_list(self, primitive):
        """ Returns the names of the properties of a primitive. """
        return getattr(self.robot, primitive).properties

    def get_primitive_property(self, primitive, property):
        """ Returns the value of a property of a primitive. """
        return self._get_register_value(primitive, property)

    def set_primitive_property(self, primitive, property, value):
        """ Sets a new value for a property of a primitive. """
        self._set_register_value(primitive, property, value)

    def get_primitive_methods_list(self, primitive):
        """ Returns the name of the methods of a primitive. """
        return getattr(self.robot, primitive).methods

    def call_primitive_method(self, primitive, method, kwargs):
        """ Calls a method of a primitive (possibly with args). """
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

    # TODO (Theo) : change names with a dic instead of ugly format
    def start_move_recorder(self, move_name, devices_name=None):
        if not hasattr(self.robot, '_{}_recorder'.format(move_name)):
            if devices_name is not None:
                devices = [getattr(self.robot, m) for m in devices_name]
            else:
                devices = self.get_devices_list()
            recorder = MoveRecorder(self.robot, 50, devices)
            self.robot.attach_primitive(recorder, '_{}_recorder'.format(move_name))
            recorder.start()
        else:
            recorder = getattr(self.robot, '_{}_recorder'.format(move_name))
            recorder.start()

    def attach_move_recorder(self, move_name, devices_name):
        devices = [getattr(self.robot, m) for m in devices_name]
        recorder = MoveRecorder(self.robot, 50, devices)
        self.robot.attach_primitive(recorder, '_{}_recorder'.format(move_name))

    def get_move_recorder_devices(self, move_name):
        try:
            recorder = getattr(self.robot, '_{}_recorder'.format(move_name))
            return [str(m.name) for m in recorder.tracked_devices]
        except AttributeError:
            return None

    def stop_move_recorder(self, move_name):
        """Allow more easily than stop_primitive() to save in a filename the recorded move"""
        recorder = getattr(self.robot, '_{}_recorder'.format(move_name))
        recorder.stop()
        with open('{}.record'.format(move_name), 'w') as f:
            recorder.move.save(f)

        # Stop player if running : to discuss
        # Recording a playing move can produce strange outputs, but could be a good feature
        try:
            player = getattr(self.robot, '_{}_player'.format(move_name))
            if player.running:
                player.stop()
        except AttributeError:
            pass

    def start_move_player(self, move_name, speed=1.0, backwards=False):
        """Move player need to have a move file
        <move_name.record> in the working directory to play it"""

        # check if running
        try:
            player = getattr(self.robot, '_{}_player'.format(move_name))
            if player.running:
                return
        except AttributeError:
            pass

        # if not running, override the play primitive
        with open('{}.record'.format(move_name)) as f:
            loaded_move = Move.load(f)
        player = MovePlayer(self.robot, loaded_move, play_speed=speed, backwards=backwards)
        self.robot.attach_primitive(player, '_{}_player'.format(move_name))

        player.start()
        return player.duration()

    def get_available_record_list(self):
        """Get list of json recorded movement files"""
        return [f.split('.record')[0] for f in os.listdir('.') if f.endswith('.record')]

    def remove_move_record(self, move_name):
        """Remove the json recorded movement file"""
        return os.remove('{}.record'.format(move_name))

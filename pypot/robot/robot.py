import logging

from ..primitive.manager import PrimitiveManager


logger = logging.getLogger(__name__)


class Robot(object):
    """ This class is used to regroup all motors and sensors of your robots.

    Most of the time, you do not want to directly instantiate this class, but you rather want to use a factory which creates a robot instance - e.g. from a python dictionnary (see :ref:`config_file`).

    This class encapsulates the different controllers (such as dynamixel ones) that automatically synchronize the virtual sensors/effectors instances held by the robot class with the real devices. By doing so, each sensor/effector can be synchronized at a different frequency.

    This class also provides a generic motors accessor in order to (more or less) easily extends this class to other types of motor.

        """
    def __init__(self, motor_controllers=[], sensor_controllers=[], sync=True):
        """
        :param list motor_controllers: motors controllers to attach to the robot
        :param list sensor_controllers: sensors controllers to attach to the robot
        :param bool sync: choose if automatically starts the synchronization loops

        """
        self._motors = []
        self._sensors = []
        self.alias = []

        self._controllers = sensor_controllers + motor_controllers

        for controller in motor_controllers:
            for m in controller.motors:
                setattr(self, m.name, m)

            self._motors.extend(controller.motors)

        for controller in sensor_controllers:
            for s in controller.sensors:
                setattr(self, s.name, s)

            self._sensors.extend(controller.sensors)

        self._attached_primitives = {}
        self._primitive_manager = PrimitiveManager(self.motors)

        self._syncing = False
        if sync:
            self.start_sync()

    def close(self):
        """ Cleans the robot by stopping synchronization and all controllers."""
        self.stop_sync()
        [c.io.close() for c in self._controllers]

    def __repr__(self):
        return '<Robot motors={}>'.format(self.motors)

    def start_sync(self):
        """ Starts all the synchonization loop (sensor/effector controllers). """
        if self._syncing:
            return

        [c.start() for c in self._controllers]
        [c.wait_to_start() for c in self._controllers]
        self._primitive_manager.start()
        self._primitive_manager._running.wait()

        self._syncing = True

        logger.info('Starting robot synchronization.')

    def stop_sync(self):
        """ Stops all the synchonization loop (sensor/effector controllers). """
        if not self._syncing:
            return

        if self._primitive_manager.running:
            self._primitive_manager.stop()

        [c.stop() for c in self._controllers]
        [s.close() for s in self.sensors if hasattr(s, 'close')]

        self._syncing = False

        logger.info('Stopping robot synchronization.')

    def attach_primitive(self, primitive, name):
        setattr(self, name, primitive)
        self._attached_primitives[name] = primitive
        primitive.name = name

        logger.info("Attaching primitive '%s' to the robot.", name)

    @property
    def motors(self):
        """ Returns all the motors attached to the robot. """
        return self._motors

    @property
    def sensors(self):
        """ Returns all the sensors attached to the robot. """
        return self._sensors

    @property
    def active_primitives(self):
        """ Returns all the primitives currently running on the robot. """
        return self._primitive_manager._prim

    @property
    def primitives(self):
        """ Returns all the primitives name attached to the robot. """
        return self._attached_primitives.values()

    @property
    def compliant(self):
        """ Returns a list of all the compliant motors. """
        return [m for m in self.motors if m.compliant]

    @compliant.setter
    def compliant(self, is_compliant):
        """ Switches all motors to compliant (resp. non compliant) mode. """
        for m in self.motors:
            m.compliant = is_compliant

    def goto_position(self, position_for_motors, duration, control=None, wait=False):
        """ Moves a subset of the motors to a position within a specific duration.

            :param dict position_for_motors: which motors you want to move {motor_name: pos, motor_name: pos,...}
            :param float duration: duration of the move
            :param str control: control type ('dummy', 'minjerk')
            :param bool wait: whether or not to wait for the end of the move

            .. note::In case of dynamixel motors, the speed is automatically adjusted so the goal position is reached after the chosen duration.

            """
        for i, (motor_name, position) in enumerate(position_for_motors.iteritems()):
            w = False if i < len(position_for_motors) - 1 else wait

            m = getattr(self, motor_name)
            m.goto_position(position, duration, control, wait=w)

    def power_up(self):
        """ Changes all settings to guarantee the motors will be used at their maximum power. """
        for m in self.motors:
            m.compliant = False
            m.moving_speed = 0
            m.torque_limit = 100.0

    def to_config(self):
        """ Generates the config for the current robot.

            .. note:: The generated config should be used as a basis and must probably be modified.

        """
        from ..dynamixel.controller import DxlController

        dxl_controllers = [c for c in self._controllers
                           if isinstance(c, DxlController)]

        config = {}

        config['controllers'] = {}
        for i, c in enumerate(dxl_controllers):
            name = 'dxl_controller_{}'.format(i)
            config['controllers'][name] = {
                'port': c.io.port,
                'sync_read': c.io._sync_read,
                'attached_motors': [m.name for m in c.motors],
            }

        config['motors'] = {}
        for m in self.motors:
            config['motors'][m.name] = {
                'id': m.id,
                'type': m.model,
                'offset': m.offset,
                'orientation': 'direct' if m.direct else 'indirect',
                'angle_limit': m.angle_limit,
            }

        config['motorgroups'] = {}

        return config

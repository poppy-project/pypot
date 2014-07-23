from numpy import rad2deg, deg2rad

from ..robot.controller import MotorsController, SensorsController


class VrepController(MotorsController):
    """ V-REP motors controller. """
    def __init__(self, vrep_io, scene, motors, sync_freq=50.):
        """
        :param vrep_io: vrep io instance
        :type vrep_io: :class:`~pypot.vrep.io.VrepIO`
        :param str scene: path to the V-REP scene file to start
        :param list motors: list of motors attached to the controller
        :param float sync_freq: synchronization frequency

        """
        MotorsController.__init__(self, vrep_io, motors, sync_freq)
        vrep_io.load_scene(scene, start=True)

    def setup(self):
        """ Setups the controller by reading/setting position for all motors. """
        self._init_vrep_streaming()

    def update(self):
        """ Synchronization update loop.

        At each update all motor position are read from vrep and set to the motors. The motors target position are also send to v-rep.

        """
        for m in self.motors:
            # Read values from V-REP and set them to the Motor
            p = round(rad2deg(self.io.get_motor_position(motor_name=m.name)), 1)
            m._values['present_position'] = p

            # Send new values from Motor to V-REP
            p = deg2rad(round(m._values['goal_position'], 1))
            self.io.set_motor_position(motor_name=m.name, position=p)

    def _init_vrep_streaming(self):
        pos = [self.io.get_motor_position(motor_name=m.name) for m in self.motors]

        for m, p in zip(self.motors, pos):
            self.io.set_motor_position(motor_name=m.name, position=p)
            m._values['goal_position'] = rad2deg(p)


class VrepObjectTracker(SensorsController):
    """ Tracks the 3D position and orientation of a V-REP object. """

    def setup(self):
        """ Forces a first update to trigger V-REP streaming. """
        self.update()

    def update(self):
        """ Updates the position and orientation of the tracked objects. """
        for s in self.sensors:
            s.position = self.io.get_object_position(object_name=s.name)
            s.orientation = self.io.get_object_orientation(object_name=s.name)

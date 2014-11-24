from numpy import rad2deg, deg2rad

from ..robot.controller import MotorsController, SensorsController
from ..robot.sensor import Sensor


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

        if scene is not None:
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
            p = round(
                rad2deg(self.io.get_motor_position(motor_name=m.name)), 1)
            m.__dict__['present_position'] = p

            # Send new values from Motor to V-REP
            p = deg2rad(round(m.__dict__['goal_position'], 1))
            self.io.set_motor_position(motor_name=m.name, position=p)

    def _init_vrep_streaming(self):
        # While the code below may look redundant and that
        # it could be simplified. It is written as such to
        # speed-up the initialization of the streaming process.
        # Here, we initalized all streaming and then wait for
        # them to be ready at once.

        # Prepare streaming for getting position for each motor
        for m in self.motors:
            self.io.call_remote_api('simxGetJointPosition',
                                    self.io.get_object_handle(m.name),
                                    streaming=True,
                                    _force=True)

        # Now actually retrieves all values
        pos = [self.io.get_motor_position(m.name) for m in self.motors]

        # Prepare streaming for setting position for each motor
        for m, p in zip(self.motors, pos):
            self.io.call_remote_api('simxSetJointTargetPosition',
                                    self.io.get_object_handle(m.name),
                                    p,
                                    sending=True,
                                    _force=True)

        # And actually affect them
        for m, p in zip(self.motors, pos):
            self.io.set_motor_position(m.name, p)
            m.__dict__['goal_position'] = rad2deg(p)


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


class VrepCollisionDetector(Sensor):

    def __init__(self, name):
        Sensor.__init__(self, name)

        self._colliding = False

    @property
    def colliding(self):
        return self._colliding

    @colliding.setter
    def colliding(self, new_state):
        self._colliding = new_state


class VrepCollisionTracker(SensorsController):

    """ Tracks collision state. """

    def setup(self):
        """ Forces a first update to trigger V-REP streaming. """
        self.update()

    def update(self):
        """ Update the state of the collision detectors. """

        for s in self.sensors:
            s.colliding = self.io.get_collision_state(collision_name=s.name)

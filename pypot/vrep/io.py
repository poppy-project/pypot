import os
import time
import ctypes

from threading import Lock

from .remoteApiBindings import vrep as remote_api
from ..robot.io import AbstractIO


vrep_error = {
    remote_api.simx_return_ok: 'Ok',
    remote_api.simx_return_novalue_flag: 'No value',
    remote_api.simx_return_timeout_flag: 'Timeout',
    remote_api.simx_return_illegal_opmode_flag: 'Opmode error',
    remote_api.simx_return_remote_error_flag: 'Remote error',
    remote_api.simx_return_split_progress_flag: 'Progress error',
    remote_api.simx_return_local_error_flag: 'Local error',
    remote_api.simx_return_initialize_error_flag: 'Init error'
}

vrep_mode = {
    'normal': remote_api.simx_opmode_oneshot_wait,
    'streaming': remote_api.simx_opmode_streaming,
    'sending': remote_api.simx_opmode_oneshot,
}


class VrepIO(AbstractIO):

    """ This class is used to get/set values from/to a V-REP scene.

        It is based on V-REP remote API (http://www.coppeliarobotics.com/helpFiles/en/remoteApiOverview.htm).

    """
    MAX_ITER = 5
    TIMEOUT = 0.4

    def __init__(self, vrep_host='127.0.0.1', vrep_port=19997, scene=None, start=False):
        """ Starts the connection with the V-REP remote API server.

        :param str vrep_host: V-REP remote API server host
        :param int vrep_port: V-REP remote API server port
        :param str scene: path to a V-REP scene file
        :param bool start: whether to start the scene after loading it

        .. warning:: Only one connection can be established with the V-REP remote server API. So before trying to connect make sure that all previously started connections have been closed (see :func:`~pypot.vrep.io.close_all_connections`)

        """
        self._object_handles = {}
        self._lock = Lock()

        self.vrep_host = vrep_host
        self.vrep_port = vrep_port
        self.scene = scene
        self.start = start

        # self.client_id = remote_api.simxStart(
        #     vrep_host, vrep_port, True, True, 5000, 5)
        # if self.client_id == -1:
        #     msg = ('Could not connect to V-REP server on {}:{}. '
        #            'This could also means that you still have '
        #            'a previously opened connection running! '
        #            '(try pypot.vrep.close_all_connections())')
        #     raise VrepConnectionError(msg.format(vrep_host, vrep_port))

        # if scene is not None:
        #     self.load_scene(scene, start)

        self.open_io()

    def open_io(self):
        self.client_id = remote_api.simxStart(
            self.vrep_host, self.vrep_port, True, True, 5000, 5)
        if self.client_id == -1:
            msg = ('Could not connect to V-REP server on {}:{}. '
                   'This could also means that you still have '
                   'a previously opened connection running! '
                   '(try pypot.vrep.close_all_connections())')
            raise VrepConnectionError(
                msg.format(self.vrep_host, self.vrep_port))

        if self.scene is not None:
            self.load_scene(self.scene, self.start)

    def close(self):
        """ Closes the current connection. """
        with self._lock:
            remote_api.simxFinish(self.client_id)

    def load_scene(self, scene_path, start=False):
        """ Loads a scene on the V-REP server.

        :param str scene_path: path to a V-REP scene file
        :param bool start: whether to directly start the simulation after loading the scene

        .. note:: It is assumed that the scene file is always available on the server side.

        """
        self.stop_simulation()

        if not os.path.exists(scene_path):
            raise IOError("No such file or directory: '{}'".format(scene_path))

        self.call_remote_api('simxLoadScene', scene_path, True)

        if start:
            self.start_simulation()

    def start_simulation(self):
        """ Starts the simulation.

            .. note:: Do nothing if the simulation is already started.

            .. warning:: if you start the simulation just after stopping it, the simulation will likely not be started. Use :meth:`~pypot.vrep.io.VrepIO.restart_simulation` instead.
        """
        self.call_remote_api('simxStartSimulation')

        # We have to force a sleep
        # Otherwise it may causes troubles??
        time.sleep(0.5)

    def restart_simulation(self):
        """ Re-starts the simulation. """
        self.stop_simulation()
        # We have to force a sleep
        # Otherwise the simulation is not restarted
        time.sleep(0.5)
        self.start_simulation()

    def stop_simulation(self):
        """ Stops the simulation. """
        self.call_remote_api('simxStopSimulation')

    def pause_simulation(self):
        """ Pauses the simulation. """
        self.call_remote_api('simxPauseSimulation')

    def resume_simulation(self):
        """ Resumes the simulation. """
        self.start_simulation()

    def get_motor_position(self, motor_name):
        """ Gets the motor current position. """
        return self.call_remote_api('simxGetJointPosition',
                                    self.get_object_handle(motor_name),
                                    streaming=True)

    def set_motor_position(self, motor_name, position):
        """ Sets the motor target position. """
        self.call_remote_api('simxSetJointTargetPosition',
                             self.get_object_handle(motor_name),
                             position,
                             sending=True)

    def get_motor_force(self, motor_name):
        """ Retrieves the force or torque applied to a joint along/about its active axis. """
        return self.call_remote_api('simxGetJointForce',
                                    self.get_object_handle(motor_name),
                                    streaming=True)

    def set_motor_force(self, motor_name, force):
        """  Sets the maximum force or torque that a joint can exert. """
        self.call_remote_api('simxSetJointForce',
                             self.get_object_handle(motor_name),
                             force,
                             sending=True)

    def get_object_position(self, object_name, relative_to_object=None):
        """ Gets the object position. """
        h = self.get_object_handle(object_name)
        relative_handle = (-1 if relative_to_object is None
                           else self.get_object_handle(relative_to_object))

        return self.call_remote_api('simxGetObjectPosition',
                                    h, relative_handle,
                                    streaming=True)

    def set_object_position(self, object_name, position=[0, 0, 0]):
        """ Sets the object position. """
        h = self.get_object_handle(object_name)

        return self.call_remote_api('simxSetObjectPosition',
                                    h, -1, position,
                                    sending=True)

    def get_object_orientation(self, object_name, relative_to_object=None):
        """ Gets the object orientation. """
        h = self.get_object_handle(object_name)
        relative_handle = (-1 if relative_to_object is None
                           else self.get_object_handle(relative_to_object))

        return self.call_remote_api('simxGetObjectOrientation',
                                    h, relative_handle,
                                    streaming=True)

    def _get_object_handle(self, obj):
        return self.call_remote_api('simxGetObjectHandle', obj)

    def get_object_handle(self, obj):
        """ Gets the vrep object handle. """
        if obj not in self._object_handles:
            self._object_handles[obj] = self._get_object_handle(obj=obj)

        return self._object_handles[obj]

    def get_collision_state(self, collision_name):
        """ Gets the collision state. """
        return self.call_remote_api('simxReadCollision',
                                    self.get_collision_handle(collision_name),
                                    streaming=True)

    def _get_collision_handle(self, collision):
        return self.call_remote_api('simxGetCollisionHandle', collision)

    def get_collision_handle(self, collision):
        """ Gets a vrep collisions handle. """
        if collision not in self._object_handles:
            h = self._get_collision_handle(collision)
            self._object_handles[collision] = h

        return self._object_handles[collision]

    def get_simulation_current_time(self, timer='CurrentTime'):
        """ Gets the simulation current time. """
        try:
            return self.call_remote_api('simxGetFloatSignal', timer, streaming=True)
        except VrepIOErrors:
            return 0.0

    def add_cube(self, name, position, sizes, mass):
        """ Add Cube """
        self._create_pure_shape(0, 239, sizes, mass, [0, 0])
        self.set_object_position("Cuboid", position)
        self.change_object_name("Cuboid", name)

    def add_sphere(self, name, position, sizes, mass, precision=[10, 10]):
        """ Add Sphere """
        self._create_pure_shape(1, 239, sizes, mass, precision)
        self.set_object_position("Sphere", position)
        self.change_object_name("Sphere", name)

    def add_cylinder(self, name, position, sizes, mass, precision=[10, 10]):
        """ Add Cylinder """
        self._create_pure_shape(2, 239, sizes, mass, precision)
        self.set_object_position("Cylinder", position)
        self.change_object_name("Cylinder", name)

    def add_cone(self, name, position, sizes, mass, precision=[10, 10]):
        """ Add Cone """
        self._create_pure_shape(3, 239, sizes, mass, precision)
        self.set_object_position("Cylinder", position)
        self.change_object_name("Cylinder", name)

    def change_object_name(self, old_name, new_name):
        """ Change object name """
        h = self._get_object_handle(old_name)
        if old_name in self._object_handles:
            self._object_handles.pop(old_name)
        lua_code = "simSetObjectName({}, '{}')".format(h, new_name)
        self._inject_lua_code(lua_code)

    def _create_pure_shape(self, primitive_type, options, sizes, mass, precision):
        """ Create Pure Shape """
        lua_code = "simCreatePureShape({}, {}, {{{}, {}, {}}}, {}, {{{}, {}}})".format(
            primitive_type, options, sizes[0], sizes[1], sizes[2], mass, precision[0], precision[1])
        self._inject_lua_code(lua_code)

    def _inject_lua_code(self, lua_code):
        """ Sends raw lua code and evaluate it wihtout any checking! """
        msg = (ctypes.c_ubyte * len(lua_code)).from_buffer_copy(lua_code.encode())
        self.call_remote_api('simxWriteStringStream', 'my_lua_code', msg)

    def call_remote_api(self, func_name, *args, **kwargs):
        """ Calls any remote API func in a thread_safe way.

        :param str func_name: name of the remote API func to call
        :param args: args to pass to the remote API call
        :param kwargs: args to pass to the remote API call

        .. note:: You can add an extra keyword to specify if you want to use the streaming or sending mode. The oneshot_wait mode is used by default (see `here <http://www.coppeliarobotics.com/helpFiles/en/remoteApiConstants.htm#operationModes>`_ for details about possible modes).

        .. warning:: You should not pass the clientId and the operationMode as arguments. They will be automatically added.

        As an example you can retrieve all joints name using the following call::

            vrep_io.remote_api_call('simxGetObjectGroupData',
                                    vrep_io.remote_api.sim_object_joint_type,
                                    0,
                                    streaming=True)

        """
        f = getattr(remote_api, func_name)

        mode = self._extract_mode(kwargs)
        kwargs['operationMode'] = vrep_mode[mode]
        # hard_retry = True

        if '_force' in kwargs:
            del kwargs['_force']
            _force = True
        else:
            _force = False

        for _ in range(VrepIO.MAX_ITER):
            with self._lock:
                ret = f(self.client_id, *args, **kwargs)

            if _force:
                return

            if mode == 'sending' or isinstance(ret, int):
                err, res = ret, None
            else:
                err, res = ret[0], ret[1:]
                res = res[0] if len(res) == 1 else res

            err = [bool((err >> i) & 1) for i in range(len(vrep_error))]

            if remote_api.simx_return_novalue_flag not in err:
                break

            time.sleep(VrepIO.TIMEOUT)

        # if any(err) and hard_retry:
        #     print "HARD RETRY"
        # self.stop_simulation() #nope
        #
        #     notconnected = True
        #     while notconnected:
        #         self.close()
        #         close_all_connections()
        #         time.sleep(0.5)
        #         try:
        #             self.open_io()
        #             notconnected = False
        #         except:
        #             print 'CONNECTION ERROR'
        #             pass
        #
        #     self.start_simulation()
        #
        #     with self._lock:
        #         ret = f(self.client_id, *args, **kwargs)
        #
        #         if mode == 'sending' or isinstance(ret, int):
        #             err, res = ret, None
        #         else:
        #             err, res = ret[0], ret[1:]
        #             res = res[0] if len(res) == 1 else res
        #
        #         err = [bool((err >> i) & 1) for i in range(len(vrep_error))]
        #
        #         return res

        if any(err):
            msg = ' '.join([vrep_error[2 ** i]
                            for i, e in enumerate(err) if e])
            raise VrepIOErrors(msg)

        return res

    def _extract_mode(self, kwargs):
        for mode in ('streaming', 'sending'):
            if mode in kwargs:
                kwargs.pop(mode)
                return mode

        return 'normal'


def close_all_connections():
    """ Closes all opened connection to V-REP remote API server. """
    remote_api.simxFinish(-1)


# V-REP Errors
class VrepIOError(Exception):

    """ Base class for V-REP IO Errors. """

    def __init__(self, error_code, message):
        message = 'V-REP error code {} ({}): "{}"'.format(
            error_code, vrep_error[error_code], message)
        Exception.__init__(self, message)


class VrepIOErrors(Exception):
    pass


class VrepConnectionError(Exception):

    """ Base class for V-REP connection Errors. """
    pass

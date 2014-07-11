import time

from functools import wraps

import vrep


from ..robot.io import AbstractIO


# V-REP decorators
class vrep_check_errorcode(object):
    """ Decorator for V-REP error code checking. """
    def __init__(self, error_msg_fmt):
        self.error_msg_fmt = error_msg_fmt

    def __call__(self, f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)

            # The decorator can be used both for Getter and Setter
            # With a Getter f returns (errorcode, return value)
            # With a Setter f returns errorcode
            err, res = (ret) if isinstance(ret, tuple) else (ret, None)

            if err != 0:
                try:
                    msg = self.error_msg_fmt.format(**kwargs)
                except KeyError:
                    msg = self.error_msg_fmt

                raise VrepIOError(err, msg)

            return res

        return wrapped_f


def vrep_init_streaming(f, vrep_timeout=0.2, max_iter=2):
    """ Decorator for initializing V-REP data streaming. """
    @wraps(f)
    def wrapped_f(*args, **kwargs):
        for _ in range(max_iter):
            err, res = f(*args, **kwargs)

            if err != vrep.simx_return_novalue_flag:
                break

            time.sleep(vrep_timeout)

        return err, res

    return wrapped_f


def vrep_init_sending(f, vrep_timeout=0.2, max_iter=2):
    """ Decorator for initializing V-REP data sending. """
    @wraps(f)
    def wrapped_f(*args, **kwargs):
        for _ in range(max_iter):
            err = f(*args, **kwargs)

            if err != vrep.simx_return_novalue_flag:
                break

            time.sleep(vrep_timeout)

        return err

    return wrapped_f


# V-REP low-level IO
class VrepIO(AbstractIO):
    """ This class is used to get/set values from/to a V-REP scene.

        It is based on V-REP remote API (http://www.coppeliarobotics.com/helpFiles/en/remoteApiOverview.htm).

    """
    def __init__(self, vrep_host='127.0.0.1', vrep_port=19997, scene=None, start=False):
        """ Starts the connection with the V-REP remote API server.

        :param str vrep_host: V-REP remote API server host
        :param int vrep_port: V-REP remote API server port
        :param str scene: path to a V-REP scene file
        :param bool start: whether to start the scene after loading it

        .. warning:: Only one connection can be established with the V-REP remote server API. So before trying to connect make sure that all previously started connections have been closed (see :func:`~pypot.vrep.io.close_all_connections`)

        """
        self.client_id = vrep.simxStart(vrep_host, vrep_port, True, True, 5000, 5)
        if self.client_id == -1:
            msg = ('Could not connect to V-REP server on {}:{}. '
                   'This could also means that you still have '
                   'a previously opened connection running! '
                   '(try pypot.vrep.close_all_connections())')
            raise VrepConnectionError(msg.format(vrep_host, vrep_port))

        self._object_handles = {}

        if scene:
            self.load_scene(scene, start)

    def close(self):
        """ Closes the current connection. """
        vrep.simxFinish(self.client_id)

    def load_scene(self, scene_path, start=False):
        """ Loads a scene on the V-REP server.

        :param str scene_path: path to a V-REP scene file
        :param bool start: whether to directly start the simulation after loading the scene

        .. note:: It is assumed that the scene file is always available on the server side.

        """
        self.stop_simulation()

        vrep.simxLoadScene(self.client_id, scene_path,
                           True, vrep.simx_opmode_oneshot_wait)

        if start:
            self.start_simulation()

    def start_simulation(self):
        """ Starts the simulation.

            .. note:: Do nothing if the simulation is already started.

            .. warning:: if you start the simulation just after stopping it, the simulation will likely not be started. Use :meth:`~pypot.vrep.io.VrepIO.restart_simulation` instead.
        """
        vrep.simxStartSimulation(self.client_id, vrep.simx_opmode_oneshot_wait)

    def restart_simulation(self):
        """ Re-starts the simulation. """
        self.stop_simulation()
        # We have to force a sleep
        # Otherwise the simulation is not restarted
        time.sleep(0.5)
        self.start_simulation()

    def stop_simulation(self):
        """ Stops the simulation. """
        vrep.simxStopSimulation(self.client_id, vrep.simx_opmode_oneshot_wait)

    def pause_simulation(self):
        """ Pauses the simulation. """
        vrep.simxPauseSimulation(self.client_id, vrep.simx_opmode_oneshot_wait)

    def resume_simulation(self):
        """ Resumes the simulation. """
        self.start_simulation()

    # Get/Set Position
    @vrep_check_errorcode('Cannot get position for "{motor_name}"')
    @vrep_init_streaming
    def get_motor_position(self, motor_name):
        """ Gets the motor current position. """
        return vrep.simxGetJointPosition(self.client_id,
                                         self.get_object_handle(obj=motor_name),
                                         vrep.simx_opmode_streaming)

    @vrep_check_errorcode('Cannot set position for "{motor_name}"')
    @vrep_init_sending
    def set_motor_position(self, motor_name, position):
        """ Sets the motor target position. """
        return vrep.simxSetJointTargetPosition(self.client_id,
                                               self.get_object_handle(obj=motor_name),
                                               position,
                                               vrep.simx_opmode_oneshot)

    @vrep_check_errorcode('Cannot get position for "{object_name}"')
    @vrep_init_streaming
    def get_object_position(self, object_name, relative_to_object=None):
        """ Gets the object position. """
        relative_handle = (-1 if relative_to_object is None
                           else self.get_object_handle(obj=relative_to_object))

        return vrep.simxGetObjectPosition(self.client_id,
                                          self.get_object_handle(obj=object_name),
                                          relative_handle,
                                          vrep.simx_opmode_streaming)

    @vrep_check_errorcode('Cannot get orientation for "{object_name}"')
    @vrep_init_streaming
    def get_object_orientation(self, object_name, relative_to_object=None):
        """ Gets the object orientation. """
        relative_handle = (-1 if relative_to_object is None
                           else self.get_object_handle(obj=relative_to_object))

        return vrep.simxGetObjectOrientation(self.client_id,
                                             self.get_object_handle(obj=object_name),
                                             relative_handle,
                                             vrep.simx_opmode_streaming)

    @vrep_check_errorcode('Cannot get handle for "{obj}"')
    def _get_object_handle(self, obj):
        return vrep.simxGetObjectHandle(self.client_id, obj,
                                        vrep.simx_opmode_oneshot_wait)

    def get_object_handle(self, obj):
        """ Gets the vrep object handle. """
        if obj not in self._object_handles:
            self._object_handles[obj] = self._get_object_handle(obj=obj)

        return self._object_handles[obj]


def close_all_connections():
    """ Closes all opened connection to V-REP remote API server. """
    vrep.simxFinish(-1)


# V-REP Errors
class VrepIOError(Exception):
    """ Base class for V-REP IO Errors. """
    def __init__(self, error_code, message):
        message = 'V-REP error code {}: "{}"'.format(error_code, message)
        Exception.__init__(self, message)


class VrepConnectionError(Exception):
    """ Base class for V-REP connection Errors. """
    pass

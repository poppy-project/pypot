import time

import vrep


from ..robot.io import AbstractIO


# V-REP decorators
class vrep_check_errorcode(object):
    """ Decorator for V-REP error code checking. """
    def __init__(self, error_msg_fmt):
        self.error_msg_fmt = error_msg_fmt

    def __call__(self, f):
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

        It is based on the V-REP remote API (http://www.coppeliarobotics.com/helpFiles/en/remoteApiOverview.htm).

    """
    def __init__(self, vrep_host='127.0.0.1', vrep_port=19997):
        """ Starts the connection with the V-REP remote API server.

        :param str vrep_host: V-REP remote API server host
        :param int vrep_port: V-REP remote API server port

        .. warning:: Only one connection can be established with the V-REP remote server API. So before trying to connect make sure that all previously started connections have been closed (see :func:`~pypot.vrep.io.close_all_connections`)

        """
        self.client_id = vrep.simxStart(vrep_host, vrep_port, True, True, 5000, 5)
        if self.client_id == -1:
            msg = ('Could not connect to V-REP server on {}:{}. '
                   'This could also means that you still have '
                   'a previously opened connection running! '
                   '(try pypot.vrep.close_all_connections())').format(vrep_host, vrep_port)
            raise VrepConnectionError(msg)

        self._motor_handles = {}

    def close(self):
        """ Close the current connection. """
        vrep.simxFinish(self.client_id)

    # Get/Set Position
    @vrep_check_errorcode('Cannot get position for "{motor_name}"')
    @vrep_init_streaming
    def get_motor_position(self, motor_name):
        """ Get the motor current position. """
        return vrep.simxGetJointPosition(self.client_id,
                                         self.get_motor_handle(motor_name=motor_name),
                                         vrep.simx_opmode_streaming)

    @vrep_check_errorcode('Cannot set position for "{motor_name}"')
    @vrep_init_sending
    def set_motor_position(self, motor_name, position):
        """ Set the motor target position. """
        return vrep.simxSetJointTargetPosition(self.client_id,
                                               self.get_motor_handle(motor_name=motor_name),
                                               position,
                                               vrep.simx_opmode_oneshot)

    @vrep_check_errorcode('Cannot get handle for "{motor_name}"')
    def _get_motor_handle(self, motor_name):
        return vrep.simxGetObjectHandle(self.client_id, motor_name,
                                        vrep.simx_opmode_oneshot_wait)

    def get_motor_handle(self, motor_name):
        """ Get the motor vrep handle. """
        if motor_name not in self._motor_handles:
            self._motor_handles[motor_name] = self._get_motor_handle(motor_name=motor_name)

        return self._motor_handles[motor_name]


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

import vrep


class VrepIOError(Exception):
    pass


class vrep_check(object):
    def __init__(self, msg):
        self.msg = msg

    def __call__(self, f):
        def safe_vrep_call(*args, **kwargs):
            val = f(*args, **kwargs)

            # If used with a getter, val should be (errorcode, retvalue)
            # If used with a setter, val should be errorcode
            errorcode, retvalue = ((val[0], val[1]) if isinstance(val, tuple)
                                   else (val, None))

            if errorcode != vrep.simx_return_ok:
                msg = '{} errorcode: {}'.format(self.msg.format(**kwargs),
                                                errorcode)
                raise VrepIOError(msg)

            return retvalue

        return safe_vrep_call


class VrepController(object):
    def __init__(self, vrep_host, vrep_port, motors):
        self.client_id = vrep.simxStart(vrep_host, vrep_port, True, True, 5000, 5)

        self._motor_handles = {m.name: self._get_motor_handle(motor_name=m.name)
                               for m in motors}

    @vrep_check('Cannot get handle for "{motor_name}"!')
    def _get_motor_handle(self, motor_name):
        return vrep.simxGetObjectHandle(self.client_id, motor_name,
                                        vrep.simx_opmode_oneshot_wait)

    # Get/Set Position

    @vrep_check('Cannot get position for "{motor_name}"')
    def _get_motor_position(self, motor_name):
        return vrep.simxGetJointPosition(self.client_id,
                                         self._motor_handles[motor_name],
                                         vrep.simx_opmode_streaming)

    @vrep_check('Cannot set position for "{motor_name}"')
    def _set_motor_position(self, motor_name, position):
        return vrep.simxSetJointTargetPosition(self.client_id,
                                               self._motor_handles[motor_name],
                                               position,
                                               vrep.simx_opmode_oneshot)

    # Get/Set Speed

    @vrep_check('Cannot get velocity for "{motor_name}"')
    def _get_motor_speed(self, motor_name):
        return vrep.simxGetObjectVelocity(self.client_id,
                                          self._motor_handles[motor_name],
                                          vrep.simx_opmode_oneshot_wait)

    @vrep_check('Cannot set velocity for "{motor_name}"')
    def _set_motor_speed(self, motor_name, speed):
        return vrep.simxSetJointTargetVelocity(self.client_id,
                                               self._motor_handles[motor_name],
                                               speed,
                                               vrep.simx_opmode_oneshot)

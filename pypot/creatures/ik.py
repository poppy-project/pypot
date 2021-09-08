from ikpy.chain import Chain
from ikpy.utils.geometry import rpy_matrix
from ikpy.urdf.URDF import get_chain_from_joints
from numpy import deg2rad, rad2deg, array, arctan2, sqrt


class IKChain(Chain):
    """ Motors chain used for forward and inverse kinematics.
    This class is based on the IK Chain as defined in the IKPY library (https://github.com/Phylliade/ikpy). It
    provides convenient methods to directly create such a chain directly from a Poppy Creature.
    """

    @classmethod
    def from_poppy_creature(cls, poppy, motors, passiv, tip, reversed_motors=[]):
        """ Creates an kinematic chain from motors of a Poppy Creature.
        :param poppy: PoppyCreature used
        :param list motors: list of all motors that composed the kinematic chain
        :param list passiv: list of motors which are passiv in the chain (they will not move)
        :param list tip: [x, y, z] translation of the tip of the chain (in meters)
        :param list reversed_motors: list of motors that should be manually reversed (due to a problem in the URDF?)
        """
        chain_elements = get_chain_from_joints(poppy.urdf_file, [m.name for m in motors])

        activ = [False] + [m not in passiv for m in motors] + [True]

        chain = cls.from_urdf_file(poppy.urdf_file,
                                   base_elements=chain_elements,
                                   last_link_vector=tip,
                                   active_links_mask=activ)

        chain.motors = [getattr(poppy, l.name) for l in chain.links[1:-1]]

        for m, l in zip(chain.motors, chain.links[1:-1]):
            # Force an access to angle limit to retrieve real values
            # This is quite an ugly fix and should be handled better
            m.angle_limit

            bounds = m.__dict__['lower_limit'], m.__dict__['upper_limit']
            l.bounds = tuple(map(rad2deg, bounds))

        chain._reversed = array([(-1 if m in reversed_motors else 1) for m in motors])

        return chain

    @property
    def joints_position(self):
        """ Returns the joints position of all motors in the chain (in degrees). """
        return [m.present_position for m in self.motors]

    # Transformation matrix M:
    # [[ Rx.x, Ry.x, Rz.x, T.x ],      R = M[:3][:3] is the rotation matrix.
    #  [ Rx.y, Ry.y, Rz.y, T.y ],
    #  [ Rx.z, Ry.z, Rz.z, T.z ],      T = M[:3][3] is the translation matrix. It corresponds
    #  [ 0   , 0   , 0,    1  ]]       to the absolute coordinates of the effector

    @property
    def position(self):
        """ Returns the cartesian position of the end of the chain (in meters). """
        angles = self.convert_to_ik_angles(self.joints_position)
        return self.forward_kinematics(angles)[:3, 3]

    @property
    def orientation(self):
        """ Returns the rotation matrix along X axis (values from -1 to 1). """
        angles = self.convert_to_ik_angles(self.joints_position)
        return self.forward_kinematics(angles)[:3, 0]

    @property
    def pose(self):
        """
        Gives the 4x4 afﬁne transformation matrix of the current position
        *Used for debug*
        :return: 4x4 afﬁne transformation matrix (float)
        """
        angles = self.convert_to_ik_angles(self.joints_position)
        return self.forward_kinematics(angles)

    @property
    def rpy(self):
        """
        Gives the rpy values of the current position
        :return: roll, pitch, yaw (float)
        """
        angles = self.convert_to_ik_angles(self.joints_position)
        R = self.forward_kinematics(angles)
        yaw = arctan2(R[2][1], R[1][1])
        pitch = arctan2(-R[3][1], sqrt(R[3][2] ^ 2 + R[3][3] ^ 2))
        roll = arctan2(R[3][2], R[3][3])
        return roll, pitch, yaw

    def rpy_to_rotation_matrix(self, r, p, y):
        """
        converts rpy to a 3x3 rotation matrix
        :param r: roll (float)
        :param p: pitch (float)
        :param y: yaw (float)
        :return: 3x3 rotation matrix
        """
        return rpy_matrix(r, p, y)

    def goto(self, position, orientation, duration, wait=False, accurate=False):
        """ Goes to a given cartesian position.
        :param list position: [x, y, z] representing the target position (in meters)
        :param list orientation: [Rx.x, Rx.y, Rx.z] transformation along X axis (values from -1 to 1)
        :param float duration: move duration
        :param bool wait: whether to wait for the end of the move
        :param bool accurate: trade-off between accurate solution and computation time. By default, use the not so
        accurate but fast version.
        """
        # if len(position) != 3:
        #     raise ValueError('Position should be a list [x, y, z]!')
        self._goto(position, orientation, duration, wait, accurate)

    def _goto(self, position, orientation, duration, wait, accurate):
        """ Goes to a given cartesian pose.
        :param matrix position: [x, y, z] representing the target position (in meters)
        :param list orientation: [Rx.x, Rx.y, Rx.z] transformation along X axis (values from -1 to 1)
        :param float duration: move duration
        :param bool wait: whether to wait for the end of the move
        :param bool accurate: trade-off between accurate solution and computation time. By default, use the not so
        accurate but fast version.
        """
        kwargs = {}
        if not accurate:
            kwargs['max_iter'] = 3

        if orientation is not None:
            shape = array(orientation).shape
            if shape == (3, 3):
                orientation_mode = "all"
            elif shape == (3,):
                orientation_mode = "X"
            else:
                orientation_mode = None
        else:
            orientation_mode = None

        # q0 = self.convert_to_ik_angles(self.joints_position)
        q = self.inverse_kinematics(target_position=position,
                                    target_orientation=orientation,
                                    orientation_mode=orientation_mode,
                                    **kwargs)

        joints = self.convert_from_ik_angles(q)

        last = self.motors[-1]
        for m, pos in list(zip(self.motors, joints)):
            m.goto_position(pos, duration, wait=False if m != last else wait)

    def convert_to_ik_angles(self, joints):
        """ Convert from poppy representation to IKPY internal representation. """
        if len(joints) != len(self.motors):
            raise ValueError('Incompatible data, len(joints) should be {}!'.format(len(self.motors)))

        raw_joints = [(j + m.offset) * (1 if m.direct else -1) for j, m in zip(joints, self.motors)]

        raw_joints *= self._reversed

        return [0] + [deg2rad(j) for j in raw_joints] + [0]

    def convert_from_ik_angles(self, joints):
        """ Convert from IKPY internal representation to poppy representation. """
        if len(joints) != len(self.motors) + 2:
            raise ValueError('Incompatible data, len(joints) should be {}!'.format(len(self.motors) + 2))

        joints = [rad2deg(j) for j in joints[1:-1]]
        joints *= self._reversed

        return [(j * (1 if m.direct else -1)) - m.offset
                for j, m in zip(joints, self.motors)]

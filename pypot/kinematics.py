import numpy

from collections import namedtuple

"""
This module can be used to compute the forward and inverse kinematics for a chain of revolute joints.
It has been largerly inspired by the Matlab Robotics Toolbox.

"""


class Link(namedtuple('Link', ('theta', 'd', 'a', 'alpha'))):
    """ Link object as defined by the standard DH representation.

    This representation is based on the following information:
    :param float theta: angle about previous z from old x to new x
    :param float d: offset along previous z to the common normal
    :param float a: offset along previous   to the common normal
    :param float alpha: angle about common normal, from old z axis to new z axis

    .. note:: We are only considering revolute joint.

    Please refer to http://en.wikipedia.org/wiki/Denavit-Hartenberg_parameters for more details.

    """

    def get_transformation_matrix(self, theta):
        """ Computes the homogeneous transformation matrix for this link. """
        ct = numpy.cos(theta + self.theta)
        st = numpy.sin(theta + self.theta)
        ca = numpy.cos(self.alpha)
        sa = numpy.sin(self.alpha)

        return numpy.matrix(((ct, -st * ca, st * sa, self.a * ct),
                             (st, ct * ca, -ct * sa, self.a * st),
                             (0, sa, ca, self.d),
                             (0, 0, 0, 1)))


class Chain(namedtuple('Chain', ('links', 'base', 'tool'))):
    """ Chain of Link that can be used to perform forward and inverse kinematics.

    :param list links: list of Link that compose the chain
    :param base: the base homogeneous transformation matrix
    :param tool: the end tool homogeneous transformation matrix

    """
    def __new__(cls, links, base=numpy.identity(4), tool=numpy.identity(4)):
        return super(Chain, cls).__new__(cls, links, base, tool)

    def forward_kinematics(self, q):
        """ Computes the homogeneous transformation matrix of the end effector of the chain.

        :param vector q: vector of the joint angles (theta 1, theta 2, ..., theta n)

        """
        q = numpy.array(q).flatten()

        if len(q) != len(self.links):
            raise ValueError('q must contain as element as the number of links')

        tr = self.base.copy()

        l = []

        for link, theta in zip(self.links, q):
            tr = tr * link.get_transformation_matrix(theta)

            l.append(tr)

        tr = tr * self.tool
        l.append(tr)
        return tr, numpy.asarray(l)

    def inverse_kinematics(self, end_effector_transformation,
                           q=None,
                           max_iter=1000, tolerance=0.05,
                           mask=numpy.ones(6),
                           use_pinv=False):
        """ Computes the joint angles corresponding to the end effector transformation.

        :param end_effector_transformation: the end effector homogeneous transformation matrix
        :param vector q: initial estimate of the joint angles
        :param int max_iter: maximum number of iteration
        :param float tolerance: tolerance before convergence
        :param mask: specify the cartesian DOF that will be ignore (in the case of a chain with less than 6 joints).
        :rtype: vector of the joint angles (theta 1, theta 2, ..., theta n)

        """
        if q is None:
            q = numpy.zeros((len(self.links), 1))
        q = numpy.matrix(q.reshape(-1, 1))

        best_e = numpy.ones(6) * numpy.inf
        best_q = None
        alpha = 1.0

        for _ in range(max_iter):
            e = numpy.multiply(transform_difference(self.forward_kinematics(q)[0], end_effector_transformation), mask)
            d = numpy.linalg.norm(e)

            if d < numpy.linalg.norm(best_e):
                best_e = e.copy()
                best_q = q.copy()
                alpha *= 2.0 ** (1.0 / 8.0)
            else:
                q = best_q.copy()
                e = best_e.copy()
                alpha *= 0.5

            if use_pinv:
                dq = numpy.linalg.pinv(self._jacob0(q)) * e.reshape((-1, 1))
            else:
                dq = self._jacob0(q).T * e.reshape((-1, 1))
            q += alpha * dq

            # d = numpy.linalg.norm(dq)
            if d < tolerance:
                return q

        else:
            raise ValueError('could not converge d={}'.format(numpy.linalg.norm(best_e)))

    def _jacob0(self, q):
        Jn = self._jacobn(q)
        Rn = rotation_from_transf(self.forward_kinematics(q)[0])

        return numpy.concatenate((numpy.concatenate((Rn, numpy.zeros((3, 3))), axis=1),
                                  numpy.concatenate((numpy.zeros((3, 3)), Rn), 1))) * Jn

    def _jacobn(self, q):
        q = numpy.array(q).flatten()
        U = self.tool.copy()
        J = numpy.matrix([[]] * 6)

        for link, theta in reversed(zip(self.links, q)):
            U = link.get_transformation_matrix(theta) * U

            d = numpy.matrix((-U[0, 0] * U[1, 3] + U[1, 0] * U[0, 3],
                              -U[0, 1] * U[1, 3] + U[1, 1] * U[0, 3],
                              -U[0, 2] * U[1, 3] + U[1, 2] * U[0, 3]))
            delta = U[2, 0:3]

            J = numpy.concatenate((numpy.concatenate((d, delta), axis=1).T, J), axis=1)

        return J


# MARK: - Utility functions

def transform_difference(t1, t2):
    t1 = numpy.array(t1)
    t2 = numpy.array(t2)

    return numpy.concatenate(((t2[0:3, 3] - t1[0:3, 3]).reshape(3),
                              0.5 * (numpy.cross(t1[0:3, 0], t2[0:3, 0]) +
                                     numpy.cross(t1[0:3, 1], t2[0:3, 1]) +
                                     numpy.cross(t1[0:3, 2], t2[0:3, 2])).reshape(3)))


def rotation_from_transf(tm):
    return tm[0:3, 0:3]


def translation_from_transf(tm):
    return numpy.array(tm[0:3, 3]).reshape(3)


def components_from_transf(tm):
    return rotation_from_transf(tm), translation_from_transf(tm)


def transf_from_components(R, T):
    return numpy.matrix(numpy.vstack((numpy.hstack((R, T.reshape(3, 1))),
                                      (0, 0, 0, 1))))


def transl(x, y, z):
    M = numpy.matrix(numpy.identity(4))
    M[0:3, 3] = numpy.matrix([x, y, z]).T
    return M


def trotx(theta):
    ct = numpy.cos(theta)
    st = numpy.sin(theta)

    R = numpy.matrix(((1, 0, 0),
                      (0, ct, -st),
                      (0, st, ct)))

    return transf_from_components(R, numpy.zeros(3))


def troty(theta):
    ct = numpy.cos(theta)
    st = numpy.sin(theta)

    R = numpy.matrix(((ct, 0, st),
                      (0, 1, 0),
                      (-st, 0, ct)))

    return transf_from_components(R, numpy.zeros(3))


def trotz(theta):
    ct = numpy.cos(theta)
    st = numpy.sin(theta)

    R = numpy.matrix(((ct, -st, 0),
                      (st, ct, 0),
                      (0, 0, 1)))

    return transf_from_components(R, numpy.zeros(3))

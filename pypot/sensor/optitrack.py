import time
import numpy
import datetime
import threading

from collections import namedtuple


TrackedObject = namedtuple('TrackedObject', ('position', 'quaternion', 'orientation', 'timestamp'))


def quat2euler(q):
    qx, qy, qz, qw = q
    sqx, sqy, sqz, sqw = q ** 2
    invs = 1.0 / (sqx + sqy + sqz + sqw)

    yaw = numpy.arctan2(2.0 * (qx * qz + qy * qw) * invs, (sqx - sqy - sqz + sqw) * invs)
    pitch = -numpy.arcsin(2.0 * (qx * qy - qz * qw) * invs)
    roll = numpy.arctan2(2.0 * (qy * qz + qx * qw) * invs, (-sqx + sqy - sqz + sqw) * invs)

    return numpy.array((yaw, pitch, roll))


try:
    import vrpn

    class OptiTrackClient(threading.Thread):
        """ Retrieves position, orientation, and timestamp of each tracked object.

            The position is expressed in meters (X is left, Y is up, and Z is depth).
            The orientation is expressed in radians (yaw, pitch, roll).

            """
        def __init__(self, addr, port, obj_names):
            threading.Thread.__init__(self)
            self.daemon = True

            self.trackers = []
            for obj in obj_names:
                t = vrpn.receiver.Tracker('{}@{}:{}'.format(obj, addr, port))
                t.register_change_handler(obj, self.handler, 'position')
                self.trackers.append(t)

            self._tracked_objects = {}

        @property
        def tracked_objects(self):
            return self._tracked_objects

        @property
        def recent_tracked_objects(self):
            """ Only returns the objects that have been tracked less than 20ms ago. """
            dt = 0.02
            f = lambda name: (datetime.datetime.now() - self.tracked_objects[name].timestamp).total_seconds()
            return dict([(k, v) for k, v in self.tracked_objects.items() if f(k) < dt])

        def handler(self, obj, data):
            self.tracked_objects[obj] = TrackedObject(numpy.array(*data['position']),
                                                      numpy.array(data['quaternion']),
                                                      quat2euler(numpy.array(data['quaternion'])),
                                                      datetime.datetime.now())

        def serve_forever(self):
            self.start()

            while True:
                try:
                    self.join(timeout=1.0)
                except KeyboardInterrupt:
                    break

        def run(self):
            while True:
                for t in self.trackers:
                    t.mainloop()
                    time.sleep(1.0 / 120)

except ImportError:
    pass

if __name__ == '__main__':
    c = OptiTrackClient('193.50.110.176', 3883, ('obj_1', ))
    c.serve_forever()

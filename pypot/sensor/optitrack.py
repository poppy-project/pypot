import vrpn
import time
import threading

from collections import namedtuple

from pypot.utils import Point, Quaternion


TrackedObject = namedtuple('TrackedObject', ('position', 'orientation'))


class OptiTrackClient(threading.Thread):
    """
        
        The position is expressed in meters (X is left, Y is up, and Z is depth).
        
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

    def handler(self, obj, data):
        self.tracked_objects[obj] = TrackedObject(Point(*data['position']),
                                                  Quaternion(*data['quaternion']))

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

if __name__ == '__main__':
    c = OptiTrackClient('193.50.110.176', 3883, ('obj_1', ))
    c.serve_forever()



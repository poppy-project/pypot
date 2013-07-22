import zmq
import threading

import pypot.sensor.optitrack as opti

from pypot.utils import Point, Quaternion


class OptiBridgeServer(threading.Thread):
    def __init__(self, bridge_host, bridge_port,
                 opti_addr, opti_port, obj_name):
        threading.Thread.__init__(self)
        self.daemon = True

        c = zmq.Context()
        self.s = c.socket(zmq.REP)
        self.s.bind('tcp://{}:{}'.format(bridge_host, bridge_port))

        self.optitrack = opti.OptiTrackClient(opti_addr, opti_port, obj_name)
        self.optitrack.start()

        self.obj_name = obj_name

    def run(self):
        while True:
            self.s.recv()
            self.s.send_json(self.optitrack.tracked_objects)


class OptiTrackClient(object):
    def __init__(self, bridge_host, bridge_port, obj_name):
        c = zmq.Context()
        self.s = c.socket(zmq.REQ)
        self.s.connect('tcp://{}:{}'.format(bridge_host, bridge_port))

        self.obj_name = obj_name

    def start(self):
        pass

    @property
    def tracked_objects(self):
        self.s.send('salut')
        d = self.s.recv_json()

        t = {}
        for name, val in d.iteritems():
            if name not in self.obj_name:
                continue
            t[name] = opti.TrackedObject(Point(*val[0]), Quaternion(*val[1]))

        return t

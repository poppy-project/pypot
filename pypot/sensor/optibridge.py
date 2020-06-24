import zmq
import time
import pickle
import threading

from . import optitrack


class OptiBridgeServer(threading.Thread):
    def __init__(self, bridge_host, bridge_port,
                 opti_addr, opti_port, obj_name):
        threading.Thread.__init__(self)
        self.daemon = True

        c = zmq.Context()
        self.s = c.socket(zmq.PUB)
        self.s.bind('tcp://{}:{}'.format(bridge_host, bridge_port))

        self.optitrack = optitrack.OptiTrackClient(opti_addr, opti_port, obj_name)
        self.optitrack.start()

        self.obj_name = obj_name

    def run(self):
        while True:
            self.s.send(pickle.dumps(self.optitrack.recent_tracked_objects))
            time.sleep(0.02)


class OptiTrackClient(threading.Thread):
    def __init__(self, bridge_host, bridge_port, obj_name):
        threading.Thread.__init__(self)
        self.daemon = True

        c = zmq.Context()
        self.s = c.socket(zmq.SUB)
        self.s.connect('tcp://{}:{}'.format(bridge_host, bridge_port))
        self.s.setsockopt(zmq.SUBSCRIBE, '')

        self.obj_name = obj_name
        self._tracked_obj = {}

    def run(self):
        while True:
            d = pickle.loads(self.s.recv())
            self._tracked_obj = {
                k: d[k]
                for k in [k for k in list(d.keys()) if k in self.obj_name]
            }

    @property
    def tracked_objects(self):
        return self._tracked_obj

    @property
    def recent_tracked_objects(self):
        return self.tracked_objects

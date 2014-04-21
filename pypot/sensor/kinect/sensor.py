import zmq
import numpy
import threading

from collections import namedtuple


from ...utils import Point3D, Point2D, Quaternion


torso_joints = ('hip_center', 'spine', 'shoulder_center', 'head')
left_arm_joints = ('shoulder_left', 'elbow_left', 'wrist_left', 'hand_left')
right_arm_joints = ('shoulder_right', 'elbow_right', 'wrist_right', 'hand_right')
left_leg_joints = ('hip_left', 'knee_left', 'ankle_left', 'foot_left')
right_leg_joints = ('hip_right', 'knee_right', 'ankle_right', 'foot_right')
skeleton_joints = torso_joints + left_arm_joints + right_arm_joints + left_leg_joints + right_leg_joints


class Skeleton(namedtuple('Skeleton', ('timestamp', 'user_id') + skeleton_joints)):
    joints = skeleton_joints


Joint = namedtuple('Joint', ('position', 'orientation', 'pixel_coordinate'))


class KinectSensor(object):
    def __init__(self, addr, port):
        self._lock = threading.Lock()
        self._skeleton = None

        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect('tcp://{}:{}'.format(addr, port))
        self.socket.setsockopt(zmq.SUBSCRIBE, '')

        t = threading.Thread(target=self.get_skeleton)
        t.daemon = True
        t.start()

    @property
    def tracked_skeleton(self):
        with self._lock:
            return self._skeleton

    @tracked_skeleton.setter
    def tracked_skeleton(self, skeleton):
        with self._lock:
            self._skeleton = skeleton

    def get_skeleton(self):
        while True:
            md = self.socket.recv_json()
            msg = self.socket.recv()

            skeleton_array = numpy.frombuffer(buffer(msg), dtype=md['dtype'])
            skeleton_array = skeleton_array.reshape(md['shape'])

            joints = []
            for i in range(len(skeleton_joints)):
                x, y, z, w = skeleton_array[i][0:4]
                position = Point3D(x / w, y / w, z / w)
                pixel_coord = Point2D(*skeleton_array[i][4:6])
                orientation = Quaternion(*skeleton_array[i][6:10])
                joints.append(Joint(position, orientation, pixel_coord))

            self.tracked_skeleton = Skeleton(md['timestamp'], md['user_index'], *joints)


if __name__ == '__main__':
    import cv2

    kinect = KinectSensor('193.50.110.60', 9999)

    while True:
        img = numpy.zeros((480, 640, 3))

        skeleton = kinect.tracked_skeleton

        if skeleton:
            for joint_name in skeleton.joints:
                x, y = getattr(skeleton, joint_name).pixel_coordinate
                pt = (int(x * 640), int(y * 480))
                cv2.circle(img, pt, 5, (255, 255, 255), thickness=-1)

        cv2.imshow('Skeleton', img)
        cv2.waitKey(50)

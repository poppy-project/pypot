import time
import itertools

import pypot.robot
import pypot.primitive


class Stand(pypot.primitive.Primitive):
    def run(self):
        print("Poppy is taking is upright posture")
        self.robot.power_max()

        # Change PID of Dynamixel MX motors
        for m in filter(lambda m: hasattr(m, 'pid'), self.robot.motors):
            m.pid = (4, 2, 0)

        # Goto to position 0 on all motors
        self.robot.goto_position(dict(zip((m.name for m in self.robot.motors),
                                            itertools.repeat(0))),
                                            2)

        # Specified some motor positions to keep the robot balanced
        self.robot.goto_position({'r_hip_z': -2,
                                'l_hip_z': 2,
                                'r_hip_x': -2,
                                'l_hip_x': 2,
                                'l_shoulder_x': 10,
                                'r_shoulder_x': -10,
                                'l_shoulder_y': 10,
                                'r_shoulder_y': 10,
                                'l_elbow_y': -20,
                                'r_elbow_y': -20,
                                'l_ankle_y': -0,
                                'r_ankle_y': -0,
                                'abs_y': -3,
                                'head_y': 0,
                                'head_z':0},
                                3,
                                wait=True)

        # Restore motor the motor speed
        self.robot.power_max()

        # Reduce max torque to keep motor temperature low
        for m in self.robot.motors:
            m.torque_limit = 70
        for m in self.robot.torso:
            m.pid = (6, 2, 0)

        # Sometimes the thread can be shutdown before the synchronization loop gets the values
        # Refer to the issue #73 on the PyPot Repository.
        time.sleep(0.5)

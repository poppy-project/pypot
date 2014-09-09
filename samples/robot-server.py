import argparse

import zerorpc

from pypot.dynamixel import autodetect_robot
from pypot.server.rest import RESTRobot

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # --configuration
    # --host
    # --port
    args = parser.parse_args()

    robot = autodetect_robot()
    robot.start_sync()

    for m in robot.motors:
        m.compliant = False

    print 'Server up and running!'

    s = zerorpc.Server(RESTRobot(robot))
    s.bind('tcp://0.0.0.0:4242')
    s.run()

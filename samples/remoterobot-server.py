import argparse

import zerorpc

from pypot.robot import from_json
from pypot.server import RESTRobot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', type=str, required=True)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('-p', '--port', type=int, default=4242)
    args = parser.parse_args()

    robot = from_json(args.config_file)
    robot.start_sync()

    rest_robot = RESTRobot(robot)

    server = zerorpc.Server(rest_robot)
    print(args.host, args.port)
    server.bind('tcp://{}:{}'.format(args.host, args.port))
    server.run()

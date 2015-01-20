import os
import json

import pypot
import poppytools

from pypot.vrep import from_vrep
from pypot.server.snap import SnapRobotServer


if __name__ == '__main__':
    # Load the robot configuration
    configfile = os.path.join(os.path.dirname(poppytools.__file__),
                              'configuration', 'poppy_config.json')

    with open(configfile) as f:
        robot_config = json.load(f)

    # Load a V-REP scene with poppy sitting
    scene = os.path.join(os.path.dirname(pypot.__file__),
                         '..', 'samples', 'notebooks', 'poppy-sitting.ttt')

    # Connect to the simulated robot
    robot = from_vrep(robot_config, '127.0.0.1', 19997, scene,
                      tracked_objects=['head_visual'])

    http = SnapRobotServer(robot, '127.0.0.1', 8080)

    snap_url = 'http://snap.berkeley.edu/snapsource/snap.html'
    blocks_url = 'http://localhost:8080/snap-blocks.xml'
    url = '{}#open:{}'.format(snap_url, blocks_url)

    print 'Snap Server should now be ready!'
    print 'You can now connect to "{}"'.format(url)

    http.run()

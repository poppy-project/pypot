import os
import time
import psutil
import argparse

from numpy import mean

from pypot.robot import from_json


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log-file',
                        type=str, required=True)
    parser.add_argument('-t', '--running-time',
                        type=int, required=True)
    parser.add_argument('-c', '--config',
                        type=str, required=True)
    args = parser.parse_args()

    bp = args.log_file
    if os.path.exists(bp):
        raise IOError('File already exists: {}'.format(bp))

    p = psutil.Process()
    p.cpu_percent()

    robot = from_json(args.config)
    robot.start_sync()
    time.sleep(60)

    loads = []
    start = time.time()
    while time.time() - start < args.running_time:
        loads.append(p.cpu_percent())
        time.sleep(1)
    load = mean(loads)
    print('After loading about {}%'.format(load))

    # We'll use raw file instead of numpy because of pypy
    with open(bp, 'w') as f:
        f.write(str(loads))

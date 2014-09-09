import os
import time
import argparse

from numpy import argmax, mean

from pypot.robot import from_json


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log-file',
                        type=str, required=True)
    parser.add_argument('-N', type=int, required=True)
    parser.add_argument('-c', '--config',
                        type=str, required=True)
    args = parser.parse_args()

    bp = args.log_file
    if os.path.exists(bp):
        raise IOError('File already exists: {}'.format(bp))

    robot = from_json(args.config)

    # We keep the controller with most motors connected
    ids = [len(c._ids) for c in robot._dxl_controllers]
    c = robot._dxl_controllers[argmax(ids)]

    print('Using controller with motors {}'.format(c._ids))

    dt = []
    for _ in range(args.N):
        start = time.time()
        c._get_pos_speed_load()
        end = time.time()
        dt.append(end - start)

    # We'll use raw file instead of numpy because of pypy
    with open(bp, 'w') as f:
        f.write(str(dt))

    print('Done in {}ms'.format(mean(dt)*1000))

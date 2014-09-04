import os
import json
import argparse

from subprocess import call, check_output

from pypot.robot import from_json

N = 50000
T = 15 * 60


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-l', '--log-folder',
                        type=str, required=True)

    parser.add_argument('-c', '--config',
                        type=str, required=True)

    args = parser.parse_args()

    bp = args.log_folder
    if os.path.exists(bp):
        raise IOError('Folder already exists: {}'.format(bp))
    os.mkdir(bp)

    call(["python", "dxl-single-motor.py",
          "-l", os.path.join(bp, 'dxl_single'),
          "-N", str(N)])

    call(["python", "dxl-controller.py",
          "-l", os.path.join(bp, 'dxl_controller.list'),
          "-N", str(N),
          "-c", args.config])

    call(["python", "robot.py",
          "-l", os.path.join(bp, 'robot.list'),
          "-t", str(T),
          "-c", args.config])

    print('Everything is done!!!')

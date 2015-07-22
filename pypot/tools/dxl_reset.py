#!/usr/bin/env python
# coding: utf-8

"""
Reset a dynamixel motor to "poppy" configuration.

This utility should only be used with a single motor connected to the bus. For the moment it's only working with robotis protocol v1 (AX, RX, MX motors).

To run it:
$ poppy-reset-motor 42

The motor will now have the id 42, use a 1000000 baud rates, a 0µs return delay time. The angle limit are also set (by default to (-180, 180)). Its position is also set to its base position (default: 0).

For more complex use cases, see:
$ poppy-reset-motor --help

"""

import logging
import time
import sys

from argparse import ArgumentParser

from pypot.dynamixel import DxlIO, get_available_ports
from pypot.dynamixel.io import DxlError


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

FACTORY_BAUDRATE = 57600
TARGET_BAUDRATE = 1000000


def leave(msg):
    print('{} Exiting now...'.format(msg))
    sys.exit(1)


def almost_equal(a, b):
    return abs(a - b) < 5.


def main():
    parser = ArgumentParser(description='Set a dynamixel motor to'
                                        ' a "poppy-like" configuration. '
                                        'Only one motor should be connected!')

    parser.add_argument(dest='id', type=int,
                        help='Dynamixel target #id.')

    parser.add_argument('-p', '--port', default='autoselect',
                        choices=get_available_ports(),
                        help='Serial port, default: autoselect')

    parser.add_argument('--log-level', default='ERROR',
                        help='Log level : CRITICAL, ERROR, WARNING, INFO, DEBUG')

    parser.add_argument('--position', type=float, default=0.0,
                        help='Position set to the motor (in degrees)')

    parser.add_argument('--angle-limit', type=float, nargs=2, default=[-180, 180],
                        help='Angle limits of the motor (in degrees)')

    args = parser.parse_args()

    if not (1 <= args.id <= 253):
        leave('Motor id should be in range [1:253]!')

    log_level = args.log_level.upper()
    logger.setLevel(log_level)

    if args.port == 'autoselect':
        try:
            # First, we make sure that there is at least one available ports
            port = get_available_ports()[0]
        except IndexError:
            leave('You need to connect at least one dynamixel port!')
    else:
        port = args.port

    print('Resetting to factory settings...')
    for br in [FACTORY_BAUDRATE, TARGET_BAUDRATE]:
        with DxlIO(port, br) as dxl:
            dxl.factory_reset()
            time.sleep(.5)
    print('Done!')

    # FACTORY_BAUDRATE and TARGET_BAUDRATE are the same for AX12
    print('Setting the motor to a "poppy" configuration')
    for br in [FACTORY_BAUDRATE, TARGET_BAUDRATE]:
        with DxlIO(port, br) as dxl:
            # We make sure that there was only one motor on the bus
            try:
                assert dxl.scan([1]) == [1]
            except AssertionError:
                leave('No motor found, check the connection!')
            except DxlError:
                leave('You should only connect one motor at'
                      ' a time when doing factory reset!')

            if args.id != 1:
                print('Changing the id to {}...'.format(args.id))
                dxl.change_id({1: args.id})

            print('Changing the return delay time to {}...'.format(0))
            dxl.set_return_delay_time({args.id: 0})
            time.sleep(.5)

            print('Changing the angle limit to {}...').format(args.angle_limit)
            dxl.set_angle_limit({args.id: args.angle_limit})
            time.sleep(.5)

            print('Changing the baudrate to {}...'.format(TARGET_BAUDRATE))
            dxl.change_baudrate({args.id: TARGET_BAUDRATE})
            time.sleep(.5)
        print('Done!')

    print('Now, checking that everything went well...')
    with DxlIO(port) as dxl:
        try:
            assert dxl.ping(args.id)
            assert dxl.get_return_delay_time([args.id]) == (0, )

        except AssertionError:
            leave('Something went wrong with the settings of "Poppy-like"'
                  ' motors configuration.\nThis is probably due to'
                  ' a communication error. Please try again.')

        lim = dxl.get_angle_limit([args.id])[0]
        if not all(map(almost_equal, lim, args.angle_limit)):
            print('Angle limit incorrect set {} instead of {}'.format(
                  lim, args.angle_limit))

        dxl.set_goal_position({args.id: args.position})
        while any(dxl.is_moving((args.id, ))):
            time.sleep(.1)

        pos = dxl.get_present_position((args.id, ))[0]
        if not almost_equal(args.position, pos):
            print('Target position not reached: {} instead of {}.'.format(
                  pos, args.position))

    print('Done!')


if __name__ == '__main__':
    main()

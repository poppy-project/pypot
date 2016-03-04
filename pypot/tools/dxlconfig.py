#!/usr/bin/env python

from __future__ import print_function

"""

Dynamixel Motor configuration.

First, it runs a factory reset. And then apply the configuration given as parameter.

*** WARNING: Make sure only motor is connected to the bus! Otherwise they will ALL be reset to their factory settings. ***

Examples:
dxlconfig --type=MX-28 --id=23 --angle-limit=(-100, 100) --zeroposition --port=/dev/ttyAMA0
dxlconfig --help

"""

import sys
import time

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from pypot.dynamixel.conversion import dynamixelModels
from pypot.dynamixel import DxlIO, Dxl320IO, get_available_ports


def check(pred, msg):
    if not pred:
        print(msg)
        print('Exiting now...')
        sys.exit(1)


def main():
    available_ports = get_available_ports()
    default_port = available_ports[0] if available_ports else None

    parser = ArgumentParser(description='Configuration tool for dynamixel motors '
                                        'WARNING: ONLY ONE MOTOR SHOULD BE '
                                        'CONNECTED TO THE BUS WHEN CONFIGURING!',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('--id', type=int, required=True,
                        help='Chosen motor id.')
    parser.add_argument('--type', type=str, required=True,
                        choices=dynamixelModels.values(),
                        help='Type of the motor to configure.')
    parser.add_argument('--port', type=str,
                        choices=available_ports, default=default_port,
                        help='Serial port connected to the motor.')
    parser.add_argument('--return-delay-time', type=int,
                        help='Set new return delay time.')
    parser.add_argument('--angle-limit', type=float, nargs=2,
                        help='Set new angle limit.')
    parser.add_argument('--goto-zero', action='store_true',
                        help='Go to zero position after configuring the motor')

    args = parser.parse_args()

    check(1 <= args.id <= 253,
          'Motor id must be in range [1:253]')

    check(available_ports,
          'Could not find an available serial port!')

    protocol = 2 if args.type in 'XL-320' else 1
    DxlIOPort = DxlIO if protocol == 1 else Dxl320IO

    # Factory Reset
    print('Factory reset...')
    if protocol == 1:
        for br in [57600, 1000000]:
            with DxlIO(args.port, baudrate=br) as io:
                io.factory_reset()
    else:
        with Dxl320IO(args.port, baudrate=1000000, timeout=0.01) as io:
            io.factory_reset(ids=range(253))
    print('Done!')

    factory_baudrate = 57600 if args.type.startswith('MX') else 1000000

    # Wait for the motor to "reboot..."
    for _ in range(10):
        with DxlIOPort(args.port, baudrate=factory_baudrate) as io:
            if io.ping(1):
                break

            time.sleep(.5)
    else:
        print('Could not communicate with the motor...')
        print('Make sure one (and only one) is connected and try again')
        sys.exit(1)

    # Switch to 1M bauds
    if args.type.startswith('MX'):
        print('Changing to 1M bauds...')
        with DxlIO(args.port, baudrate=factory_baudrate) as io:
            io.change_baudrate({1: 1000000})

        time.sleep(.5)
        print('Done!')

    # Change id
    print('Changing id to {}...'.format(args.id))
    if args.id != 1:
        with DxlIOPort(args.port) as io:
            io.change_id({1: args.id})

            time.sleep(.5)
            check(io.ping(args.id),
                  'Could not change id to {}'.format(args.id))
    print('Done!')

    # Set return delay time
    if args.return_delay_time is not None:
        print('Changing return delay time to {}...'.format(args.return_delay_time))
        with DxlIOPort(args.port) as io:
            io.set_return_delay_time({args.id: args.return_delay_time})

            time.sleep(.5)
            check(io.get_return_delay_time([args.id])[0] == args.return_delay_time,
                  'Could not set return delay time to {}'.format(args.return_delay_time))
        print('Done!')

    # Set Angle Limit
    if args.angle_limit is not None:
        print('Changing angle limit to {}...'.format(args.angle_limit))
        with DxlIOPort(args.port) as io:
            io.set_angle_limit({args.id: args.angle_limit})

            time.sleep(.5)
            check(all(map(lambda p1, p2: abs(p1 - p2) < 1.,
                      io.get_angle_limit([args.id])[0],
                      args.angle_limit)),
                  'Could not change angle limit to {}'.format(args.angle_limit))
        print('Done!')

    # GOTO ZERO
    if args.goto_zero:
        print('Going to position 0...')
        with DxlIOPort(args.port) as io:
            io.set_moving_speed({args.id: 100.0})
            io.set_goal_position({args.id: 0.0})

            time.sleep(2.0)
            check(abs(io.get_present_position([args.id])[0]) < 5,
                  'Could not go to 0 position')

        print('Done!')


if __name__ == '__main__':
    main()

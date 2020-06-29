#!/usr/bin/env python



"""
Poppy configuration tools

Examples:
* poppy-configure ergo-jr m2

"""
import sys

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from subprocess import call

from pypot.creatures import installed_poppy_creatures
from pypot.utils import flushed_print as print


def find_port_for_motor(config, motor):
    def flatten_motorgroups(motors, groups):
        l = []
        for m in motors:
            if m in groups:
                l += flatten_motorgroups(groups[m], groups)
            else:
                l.append(m)
        return l
    
    for bus in config['controllers']:
        motors_on_bus = config['controllers'][bus]["attached_motors"]
        motors = flatten_motorgroups(motors_on_bus, config['motorgroups'])
        if motor in motors:
            return config['controllers'][bus]["port"]

    raise ValueError('Something must be wrong in your configuration file. '
                     'Could not find bus for motor {}'.format(motor))


def main():
    robots = [c.replace('poppy-', '') for c in installed_poppy_creatures]

    parser = ArgumentParser(description='Configuration tool for Poppy robots ',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('robot', type=str, choices=robots,
                        help='Robot used.')

    parser.add_argument('motor', type=str,
                        help='Name of the motor to configure.')

    args = parser.parse_args()

    RobotCls = installed_poppy_creatures['poppy-{}'.format(args.robot)]
    c = RobotCls.default_config

    if args.motor not in c['motors']:
        print('"{}" is not a motor of "{}"! '
              'possibilities={}'.format(args.motor, args.robot,
                                        sorted(c['motors'].keys())))
        print('Exiting now...')
        sys.exit(1)

    motor_config = c['motors'][args.motor]

    args = [
        '--id', motor_config['id'],
        '--type', motor_config['type'],
        '--port', find_port_for_motor(c, args.motor),
        '--return-delay-time', 0
    ]
    
    if 'wheel_mode' in motor_config.keys():
        args.extend(('--wheel-mode', motor_config['wheel_mode']))
    else:
        args.extend(('--angle-limit',motor_config['angle_limit'][0],motor_config['angle_limit'][1],
                     '--goto-zero'))
        
    call(['dxl-config'] + list(map(str, args)))


if __name__ == '__main__':
    main()

#!/usr/bin/env python

from __future__ import print_function

import sys
import time
import random
import logging
import argparse
import webbrowser

from contextlib import closing
from argparse import RawTextHelpFormatter

from pypot.utils.network import find_local_ip
from pypot.creatures import installed_poppy_creatures


def start_poppy_with_services(args):
    params = poppy_params_from_args(args)

    for i in range(5):
        try:
            print('Attempt {} to start the robot...'.format(i + 1))
            return installed_poppy_creatures[args.creature](**params)

        except Exception as e:
            # In case of failure,
            # Give the robot some time to statup, reboot...
            time.sleep(random.random())
            print(e)
            exc_type, exc_inst, tb = sys.exc_info()
    else:
        print('Could not start up the robot...')

        # Re-raise the last exception allow to show traceback
        # and debug the potiential code issue
        raise exc_inst
        sys.exit(1)


def poppy_params_from_args(args):
    params = {
        'serve_http_api': args.http,
        'http_api_port': args.http_port,
        'use_remote': args.remote
    }

    if args.snap:
        params['serve_http_api'] = True

    if args.verbose:
        params['http_api_debug'] = False

    if args.vrep:
        params['simulator'] = 'vrep'
    elif args.poppy_simu:
        params['simulator'] = 'poppy-simu'

    if args.disable_camera:
        params['camera'] = 'dummy'

    return params


def main():
    parser = argparse.ArgumentParser(
        description=('Poppy services launcher. Use it to quickly instantiate a ' +
                     'poppy creature with Snap!, an http server, or a remote robot.'),
        epilog="""
Examples:
* poppy-services --snap poppy-torso
* poppy-services --snap --vrep poppy-humanoid""",
        formatter_class=RawTextHelpFormatter)

    parser.add_argument('creature', type=str,
                        help='poppy creature name',
                        action='store', nargs='?',
                        choices=installed_poppy_creatures.keys())
    parser.add_argument('--vrep',
                        help='use a V-REP simulated Poppy Creature',
                        action='store_true')
    parser.add_argument('--poppy-simu',
                        help='use a Three.js visualization',
                        action='store_true')
    parser.add_argument('--snap',
                        help='make sure the HTTP API is launched for Snap!',
                        action='store_true')
    parser.add_argument('-nb', '--no-browser',
                        help='avoid automatic start of Snap! in web browser',
                        action='store_true')
    parser.add_argument('--http',
                        help='start a HTTP API robot server',
                        action='store_true')
    parser.add_argument('--http-port',
                        help='port of HttpRobotServer',
                        default=6969, type=int)
    parser.add_argument('--remote',
                        help='start a remote robot server',
                        action='store_true')
    parser.add_argument('--disable-camera',
                        help='Start the robot without the camera.',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='start services with verbose mode. There is 3 debug levels, add as "v" as debug level you want',
                        action='count')
    parser.add_argument('-f', '--log-file',
                        help='Log filename',
                        action='store')

    nb_creatures = len(installed_poppy_creatures.keys())
    if nb_creatures == 0:
        print('No installed poppy creature were found!')
        print('You should first install the python package '
              'corresponding to your robot or check your python environment.')
        sys.exit(1)

    args = parser.parse_args()

    # If no creature are specified and only one is installed
    # We use it as default.
    if args.creature is None:
        if nb_creatures > 1:
            parser.print_help()
            sys.exit(1)

        args.creature = installed_poppy_creatures.keys()[0]
        print('No creature specified, use {}'.format(args.creature))

    if args.log_file:
        fh = logging.FileHandler(args.log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger('').addHandler(fh)

    if args.verbose:
        if args.verbose == 1:
            lvl = logging.WARNING
        elif args.verbose == 2:
            lvl = logging.INFO
        elif args.verbose > 2:
            lvl = logging.DEBUG

        if args.log_file is not None:
            ch = logging.FileHandler(args.log_file)
        else:
            ch = logging.StreamHandler()

        ch.setLevel(lvl)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch.setFormatter(formatter)
        logging.getLogger('').addHandler(ch)

    if not any([args.snap, args.http, args.remote, args.poppy_simu]):
        print('No service specified! See --help for details.')
        sys.exit(1)

    if args.snap and not args.no_browser:
        snap_url = 'http://snap.berkeley.edu/snapsource/snap.html'
        # TODO: we still need a rule for serving snap project filename
        # if we want to keep this feature.
        block_url = 'http://{}:{}/snap-blocks.xml'.format(find_local_ip(),
                                                          args.http_port)
        url = '{}#open:{}'.format(snap_url, block_url)

        for browser_name in ['chromium-browser', 'chromium', 'google-chrome',
                             'chrome', 'safari', 'midori', None]:
            try:
                browser = webbrowser.get(browser_name)
                browser.open(url, new=0, autoraise=True)
                break
            except:
                pass

    with closing(start_poppy_with_services(args)):
        print('Robot created and running!')
        sys.stdout.flush()

        # Just run4ever (until Ctrl-c...)
        try:
            while(True):
                time.sleep(1000)
        except KeyboardInterrupt:
            print("Bye bye!")


if __name__ == '__main__':
    main()

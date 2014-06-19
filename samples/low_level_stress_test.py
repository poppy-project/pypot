"""
Stress test of the low-level communication with dynamixel motors.

This script will test how fast is your low-level communication with a single dynamixel motor.
For performance issue, the motor should be configured as follows:
* baudrate set to 1000000
* return delay time set to 0

"""

import itertools
import datetime
import argparse
import profile
import numpy
import time
import sys
import os

import pypot.dynamixel

from pypot.dynamixel.packet import DxlReadDataPacket, DxlSyncWritePacket
from pypot.dynamixel.conversion import dxl_code


BAUDRATE = 1000000
N = 1000


def leave(msg):
    print('*** {} *** Test failed!!!'.format(msg))
    sys.exit(1)


def my_timeit(f, n):
    dt = []

    for _ in range(n):
        start = time.time()
        f()
        end = time.time()
        dt.append(end - start)

    return numpy.array(dt)


def my_profile(f, n, filename):
    profile.run('[{}() for _ in range({})]'.format(f, n), filename)


def prof(f_name, n, log_folder):
    basename = os.path.join(log_folder, f_name)

    t = my_timeit(globals()[f_name], n)
    numpy.save('{}.npy'.format(basename), t)

    my_profile(f_name, n, '{}.prof'.format(basename))
    return t * 1000

if __name__ == '__main__':
    available_ports = pypot.dynamixel.get_available_ports()
    log_folder = 'log_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Stress test of the low-level communication'
                                     ' with dynamixel motors.')

    parser.add_argument('-p', '--port',
                        type=str,
                        choices=available_ports,
                        default=available_ports[0] if available_ports else None,
                        help='Select which port to test')

    parser.add_argument('-i', '--id',
                        type=int,
                        help='Select which motor to test')

    parser.add_argument('-n', '--nb-run',
                        type=int, default=N,
                        help='Number of read/write to do')

    parser.add_argument('-o', '--log-folder',
                        type=str, default=log_folder,
                        help='Name of the output log folder')

    args = parser.parse_args()

    if os.path.exists(args.log_folder):
        leave('Log folder already exists')

    os.mkdir(args.log_folder)

    if not args.port:
        leave('No available dynamixel port found!')

    print('Connecting on port {} with baudrate {}.'.format(args.port, BAUDRATE))
    dxl = pypot.dynamixel.DxlIO(args.port, baudrate=BAUDRATE)
    print('Done!')

    if not args.id:
        print('Scanning motors on the bus...')
        ids = dxl.scan()

        if not ids:
            leave('No motor where found on the bus!')

        print('Found ids: {}'.format(ids))
        args.id = ids[0]

    print('Testing motor {}'.format(args.id))
    if not dxl.ping(args.id):
        leave('Can\'t ping motor {}'.format(args.id))

    ids = [args.id]

    if dxl.get_return_delay_time(ids)[0] != 0:
        leave('Set the return delay time of the motor to 0')

    print('Start testing...')

    def rw_pypot():
        dxl.get_present_position(ids)
        dxl.set_goal_position(dict(zip(ids, itertools.repeat(0))))

    print('Testing with pypot read/write...')
    t = prof('rw_pypot', args.nb_run, args.log_folder)
    print ('Done in {}ms (STD={})'.format(numpy.mean(t), numpy.std(t)))

    c_get = [c for c in pypot.dynamixel.DxlIO._DxlIO__controls
             if c.name == 'present position'][0]

    c_set = [c for c in pypot.dynamixel.DxlIO._DxlIO__controls
             if c.name == 'goal position'][0]

    pos = dxl_code(0, c_set.length)
    rp = DxlReadDataPacket(ids[0], c_get.address, c_get.length)
    sp = DxlSyncWritePacket(c_set.address, c_set.length, ids[:1] + list(pos))

    def rw_forged_packet():
        dxl._send_packet(rp)
        dxl._send_packet(sp, wait_for_status_packet=False)

    print('Testing with pref-forged packed...')
    t = prof('rw_forged_packet', args.nb_run, args.log_folder)
    print ('Done in {}ms (STD={})'.format(numpy.mean(t), numpy.std(t)))

    s_read = rp.to_string()
    s_write = sp.to_string()

    def rw_serial():
        dxl._serial.write(s_read)
        dxl._serial.read(8)
        dxl._serial.write(s_write)

    print('Testing with direct serial read/write...')
    t = prof('rw_serial', args.nb_run, args.log_folder)
    print ('Done in {}ms (STD={})'.format(numpy.mean(t), numpy.std(t)))

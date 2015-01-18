import os
import time
import numpy
import argparse
import itertools

from pypot.dynamixel import DxlIO, get_available_ports
from pypot.dynamixel.packet import DxlReadDataPacket, DxlSyncWritePacket
from pypot.dynamixel.conversion import dxl_code


def timeit(rw_func, N, destfile):
    dt = []
    for _ in range(N):
        start = time.time()
        rw_func()
        end = time.time()

        dt.append(end - start)

    # We'll use raw file instead of numpy because of pypy
    with open(destfile, 'w') as f:
        f.write(str(dt))

    return numpy.mean(dt)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log-folder',
                        type=str, required=True)
    parser.add_argument('-N', type=int, required=True)
    args = parser.parse_args()

    bp = args.log_folder
    if os.path.exists(bp):
        raise IOError('Folder already exists: {}'.format(bp))
    os.mkdir(bp)

    available_ports = get_available_ports()

    port = available_ports[0]
    print('Connecting on port {}.'.format(port))
    dxl = DxlIO(port)

    print('Scanning motors on the bus...')
    ids = dxl.scan()
    print('Found {}'.format(ids))

    ids = ids[:1]
    print('Will use id: {}'.format(ids))

    if dxl.get_return_delay_time(ids)[0] != 0:
        raise IOError('Make sure your motor has return delay time set to 0')

    print('Start testing !')

    print('Using "normal" pypot package...')
    def rw_pypot():
        dxl.get_present_position(ids)
        dxl.set_goal_position(dict(zip(ids, itertools.repeat(0))))

    dt = timeit(rw_pypot, args.N, os.path.join(bp, 'rw_pypot.list'))
    print('in {}ms'.format(dt * 1000))

    print('Using pref-forged packet...')
    c_get = [c for c in DxlIO._DxlIO__controls
             if c.name == 'present position'][0]

    c_set = [c for c in DxlIO._DxlIO__controls
             if c.name == 'goal position'][0]

    pos = dxl_code(0, c_set.length)
    rp = DxlReadDataPacket(ids[0], c_get.address, c_get.length)
    sp = DxlSyncWritePacket(c_set.address, c_set.length, ids[:1] + list(pos))

    def rw_forged_packet():
        dxl._send_packet(rp)
        dxl._send_packet(sp, wait_for_status_packet=False)

    dt = timeit(rw_forged_packet, args.N, os.path.join(bp, 'rw_forged.list'))
    print('in {}ms'.format(dt * 1000))

    print('Using raw serial communication...')
    s_read = rp.to_string()
    s_write = sp.to_string()

    def rw_serial():
        dxl._serial.write(s_read)
        dxl._serial.read(8)
        dxl._serial.write(s_write)
    dt = timeit(rw_serial, args.N, os.path.join(bp, 'rw_serial.list'))
    print('in {}ms'.format(dt * 1000))

    print('Done !')

import argparse
import numpy
import time
import sys

import pypot.dynamixel

N = 1000


def read_register(dxl, register, ids):
    print('\tReading {} times the {}...'.format(N, register))

    t = []
    getter = getattr(dxl, 'get_{}'.format(register))

    for _ in range(N):
        start = time.time()
        getter(ids)
        end = time.time()
        t.append(1000 * (end - start))

    print('\tTook {}ms (STD={}) per read'.format(numpy.mean(t), numpy.std(t)))


def full_test(dxl, ids):
    print('Testing the communication speed with motor{} {}'.format('s' if len(ids) else '',
                                                                   ids))
    read_register(dxl, 'present_position', ids)
    read_register(dxl, 'control_table', ids)


if __name__ == '__main__':
    available_ports = pypot.dynamixel.get_available_ports()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Test low-level communication with Dynamixel motors.')

    parser.add_argument('-p', '--ports',
                        type=str, nargs='+',
                        default=available_ports,
                        help='Select which port(s) to test')

    parser.add_argument('-b', '--baudrate',
                        type=int, choices=[57600, 1000000], default=1000000,
                        help='Sets the baudrate')

    args = parser.parse_args()

    for port in args.ports:
        print('Now testing port {} with {}bds...'.format(port, args.baudrate))

        print('Opening connection...')
        with pypot.dynamixel.DxlIO(port, baudrate=args.baudrate) as dxl:
            print('Ok!')
            print('Scanning the bus...',)
            sys.stdout.flush()
            ids = dxl.scan()
            print('Done!')
            print('Ids found: {}'.format(ids))

            full_test(dxl, ids[:1])
            full_test(dxl, ids)

        print('Closing port')

#!/usr/bin/env python
# coding: utf-8
"""
Reset un dynamixel et lui affecte un nouvel id,

Mode d'emploi:

Connecter un actuateur unique est sur le bus dynamixel et lancer:
$ ./dxl-init.py 42
Le moteur porte maintenant le n°42 et répond à la poppy-vitesse de 1000000 bauds,
de plus sa position est remise à zéro.

Testé avec:
    MX-64
    MX-28
    AX-12
"""

from pypot.dynamixel import DxlIO, get_available_ports
from pypot.dynamixel.io.abstract_io import DxlTimeoutError
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""Default settings"""
FACTORY_BAUDRATE = 57142

"""Poppy software settings"""
TARGET_BAUDRATE = 1000000

def send_reset(port,baudrate):
    """
    Broadcasts a reset on given port/baudrate
    """
    dxl = DxlIO(port,baudrate=baudrate)
    proto = dxl._protocol
    msg = proto.DxlInstructionPacket(id=proto.DxlBroadcast, instruction=0x06,
                                     parameters=[])
    try:
        dxl._send_packet(msg, error_handler=None)
    except DxlTimeoutError as e:
        pass
    finally:
        dxl.close()


if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Sets dynamixel id and baudrate')
    parser.add_argument('-p','--port',dest='port',default=None,nargs='?',
                        help='Serial port, default: autoselect')
    parser.add_argument('--log-level', default='INFO',
                        help='Log level : CRITICAL, ERROR, WARNING, INFO, DEBUG')
    parser.add_argument(dest='id',help='Dynamixel #id.')
    args = parser.parse_args()

    log_level = args.log_level.upper()
    logger.setLevel(log_level)

    if args.port is None:
        ports = get_available_ports()
        if not len(ports):
            logger.error('No available ports')
            sys.exit(1)
        setattr(args,'port',ports[0])

    """
    Note: les appels à sleep() peuvent sans doute être remplacés par des flush
          ou des accusés de réception des actuateurs.
    """
    for br in [TARGET_BAUDRATE, FACTORY_BAUDRATE]:
        logger.info('Braodcast reset at baudrate = {}'.format(br))
        send_reset(args.port,br)
        sleep(0.2)

    dxl = DxlIO(args.port,baudrate=FACTORY_BAUDRATE)
    if dxl.ping(1):
        # AX-12 factory default = 1000000 bps
        dxl.change_baudrate({1:TARGET_BAUDRATE})
    dxl.close()
    sleep(0.2)

    target_id = int(args.id)

    dxl = DxlIO(args.port,baudrate=TARGET_BAUDRATE)

    dxl.switch_led_on((1,))
    dxl.change_id({1:target_id})
    sleep(0.1)

    # test move
    #dxl.set_goal_position({target_id:60})
    #while dxl.is_moving((target_id,))[0]:
    #    pass

    dxl.set_goal_position({target_id:0})
    while dxl.is_moving((target_id,))[0]:
        pass
    sleep(0.1) # sans ce sleep, la led reste allumée
    dxl.switch_led_off((target_id,))
    dxl.close()

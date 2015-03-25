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

def do_reset(dxl,baudrate):
    """
    Broadcasts a reset on given DxlIO / baudrate
    """
    reset_msg = dxl._protocol.DxlInstructionPacket(id=dxl._protocol.DxlBroadcast,
                                                instruction=0x06, parameters=[])

    logger.info('Broadcast reset at baudrate = {}'.format(br))
    setattr(dxl,'baudrate',br) # calls AbstractIO.baudrate setter
    try:
        dxl._send_packet(reset_msg, error_handler=None)
    except DxlTimeoutError as e:
        pass



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

    with DxlIO(args.port) as dxl:
        for br in [TARGET_BAUDRATE, FACTORY_BAUDRATE]:
            do_reset(dxl,br)
            sleep(0.25)

        setattr(dxl,'baudrate',FACTORY_BAUDRATE)
        if dxl.ping(1):
            # AX-12 factory default = 1000000 bps
            dxl.change_baudrate({1:TARGET_BAUDRATE})
            sleep(0.25)

    with DxlIO(args.port, baudrate=TARGET_BAUDRATE) as dxl:
            target_id = int(args.id)
            sleep(0.25)

            dxl.switch_led_on((1,))
            sleep(0.25)

            dxl.change_id({1:target_id})
            sleep(0.25)

            ## test move
            #dxl.set_goal_position({target_id:60})
            #while dxl.is_moving((target_id,))[0]:
            #    pass

            dxl.set_goal_position({target_id:0})
            while dxl.is_moving((target_id,))[0]:
                pass

            sleep(0.1) # sans ce sleep, la led reste allumée
            dxl.switch_led_off((target_id,))

# -*- coding: utf-8 -*-

import numpy
import itertools

from collections import namedtuple


HkxBroadcast = 254


class HkxInstruction(object):
    EEP_WRITE = 0x01
    EEP_READ = 0x02
    RAM_WRITE = 0x03
    RAM_READ = 0x04
    I_JOG = 0x05
    S_JOG = 0x06
    STAT = 0x07
    ROLLBACK = 0x08
    REBOOT = 0x09


# MARK: - Packet Header

class HkxPacketHeader(namedtuple('HkxPacketHeader', ('packet_length', 'id'))):
    """ This class represents the header of a Hkx Packet.

        They are constructed as follows [0xFF, 0xFF, LENGTH, ID] where:
            * ID represents the ID of the motor who received (resp. sent) the intruction (resp. status) packet.
            * LENGTH represents the length of the rest of the packet

        """
    length = 4
    marker = bytearray((0xFF, 0xFF))

    @classmethod
    def from_string(cls, data):
        header = bytearray(data)

        if len(header) != cls.length or header[:len(cls.marker)] != cls.marker:
            raise ValueError('try to parse corrupted data ({})'.format(header))
        
        return cls(header[2], header[3])


# MARK: - Instruction Packet

class HkxInstructionPacket(namedtuple('HkxInstructionPacket',
                                      ('id', 'instruction', 'parameters'))):
    """ This class is used to represent a herkulex instruction packet.

        An instruction packet is constructed as follows:
        [0xFF, 0xFF, SIZE, ID, INSTRUCTION, CHECKSUM1, CHECKSUM2, PARAM 1, PARAM 2, ..., PARAM N]

        """
    def to_array(self):
        return bytearray(itertools.chain(HkxPacketHeader.marker,
                                         (self.size, self.id, self.instruction),
                                         self.checksums,
                                         self.parameters
                                         ))

    def to_string(self):
        return bytes(self.to_array())

    @property
    def size(self):
        return len(self.parameters) + 7

    @property
    def checksums(self):
        check1= self.size ^ self.id ^ self.instruction
        for t in self.parameters:
            check1 = check1 ^ t
        check1 = check1 & 0xFE
        return (check1, (~check1) & 0xFE)


class HkxPingPacket(HkxInstructionPacket):
    """ This class is used to represent ping packet. """
    def __new__(cls, id):
        return HkxInstructionPacket.__new__(cls, id, HkxInstruction.STAT, ())

    def __repr__(self):
        return 'HkxPingPacket(id={})'.format(self.id)

class HkxRollBackPacket(HkxInstructionPacket):
    """ This class is used to represent reset packet. """
    def __new__(cls):
        return HkxInstructionPacket.__new__(cls, HkxBroadcast,
                                            HkxInstruction.ROLLBACK, (0,0))


class HkxReadDataPacket(HkxInstructionPacket):
    """ This class is used to represent read data packet (to read value) """
    def __new__(cls, id, eeprom_ram, address, length):
        instruct = HkxInstruction.RAM_READ
        if(eeprom_ram) == 'EEPROM':
            instruct = HkxInstruction.EEP_READ
        return HkxInstructionPacket.__new__(cls, id,
                                            instruct,
                                            (address, length))

    def __repr__(self):
        return ('HkxReadDataPacket(id={}, '
                'address={}, total length={}, value={})'.format(self.id,
                                               self.parameters[0],
                                               self.parameters[1],
                                               self.parameters[2:]))


class HkxWriteDataPacket(HkxInstructionPacket):
    """ This class is used to represent write data packet (to write value) """
    def __new__(cls, id, eeprom_ram, address, length, nb_elem, coded_value):
        instruct = HkxInstruction.RAM_WRITE
        if(eeprom_ram) == 'EEPROM':
            instruct = HkxInstruction.EEP_WRITE
        return HkxInstructionPacket.__new__(cls, id,
                                            instruct,
                                            tuple(itertools.chain((address, length * nb_elem),
                                                                  coded_value)))

    def __repr__(self):
        return ('HkxWriteDataPacket(id={}, '
                'address={}, total length={}, value={})'.format(self.id,
                                               self.parameters[0],
                                               self.parameters[1],
                                               self.parameters[2:]))

class HkxJogPacket(HkxInstructionPacket):
    """ This class is used to represent jog packets  """
    def __new__(cls, id, jog_type, coded_value):
        return HkxInstructionPacket.__new__(cls, id,
                                            HkxInstruction.I_JOG,
                                            coded_value)

    def __repr__(self):
        return ('HkxJogPacket(id={}, '
                'instruction={}, parameters={})'.format(self.id,
                                        self.instruction,
                                        self.parameters[0:]))


# MARK: - Status Packet
class HkxStatusPacket(namedtuple('HkxStatusPacket', ('id', 'instruction', 'parameters', 'error', 'status_detail'))):
    """ This class is used to represent a herculex status packet.

        A status packet is constructed as follows:
        [0xFF, 0xFF, SIZE, ID, INSTRUCTION, CHECKSUM1, CHECKSUM2, PARAM 1, PARAM 2, ..., PARAM N, STATUS ERROR, STATUS DETAIL]

        """
    @classmethod
    def from_string(cls, data):
        packet = bytearray(data)
        header = HkxPacketHeader.from_string(packet[:4])
        #TODO add checksum test
        if len(packet) != header.packet_length :
            raise ValueError('try to parse corrupted data ({})'.format(packet))

        return cls(header.id, packet[4], tuple(packet[9:-2]), packet[-2], packet[-1])
    
    def __repr__(self):
        return ('HkxStatusPacket(id={}, '
                'instruction={}, parameters={}, error={}, status detail={})'.format(self.id,
                                        self.instruction,
                                        self.parameters,
                                        self.error,
                                        self.status_detail))

# -*- coding: utf-8 -*-

import numpy
import itertools

from collections import namedtuple

name = 'v1'

DxlBroadcast = 254


class DxlInstruction(object):
    PING = 0x01
    READ_DATA = 0x02
    WRITE_DATA = 0x03
    RESET = 0x06
    SYNC_WRITE = 0x83
    SYNC_READ = 0x84


# MARK: - Packet Header

class DxlPacketHeader(namedtuple('DxlPacketHeader', ('id', 'packet_length'))):
    """ This class represents the header of a Dxl Packet.

        They are constructed as follows [0xFF, 0xFF, ID, LENGTH] where:
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

class DxlInstructionPacket(namedtuple('DxlInstructionPacket',
                                      ('id', 'instruction', 'parameters'))):
    """ This class is used to represent a dynamixel instruction packet.

        An instruction packet is constructed as follows:
        [0xFF, 0xFF, ID, LENGTH, INSTRUCTION, PARAM 1, PARAM 2, ..., PARAM N, CHECKSUM]

        (for more details see http://support.robotis.com/en/product/dxl_main.htm)

        """
    def to_array(self):
        return bytearray(itertools.chain(DxlPacketHeader.marker,
                                         (self.id, self.length, self.instruction),
                                         self.parameters,
                                         (self.checksum, )))

    def to_string(self):
        return bytes(self.to_array())

    @property
    def length(self):
        return len(self.parameters) + 2

    @property
    def checksum(self):
        return int(255 - ((self.id + self.length + self.instruction +
                           sum(self.parameters)) % 256))


class DxlPingPacket(DxlInstructionPacket):
    """ This class is used to represent ping packet. """
    def __new__(cls, id):
        return DxlInstructionPacket.__new__(cls, id, DxlInstruction.PING, ())

    def __repr__(self):
        return 'DxlPingPacket(id={})'.format(self.id)


class DxlResetPacket(DxlInstructionPacket):
    """ This class is used to represent reset packet. """
    def __new__(cls):
        return DxlInstructionPacket.__new__(cls, DxlBroadcast,
                                            DxlInstruction.RESET, ())


class DxlReadDataPacket(DxlInstructionPacket):
    """ This class is used to represent read data packet (to read value). """
    def __new__(cls, id, address, length):
        return DxlInstructionPacket.__new__(cls, id,
                                            DxlInstruction.READ_DATA,
                                            (address, length))

    def __repr__(self):
        return ('DxlReadDataPacket(id={}, address={}'
                ', length={})'.format(self.id,
                                      self.parameters[0],
                                      self.parameters[1]))


class DxlSyncReadPacket(DxlInstructionPacket):
    """ This class is used to represent sync read packet (to synchronously read values). """
    def __new__(cls, ids, address, length):
        return DxlInstructionPacket.__new__(cls, DxlBroadcast,
                                            DxlInstruction.SYNC_READ,
                                            tuple(itertools.chain((address, length),
                                                                  ids)))

    def __repr__(self):
        return ('DxlSyncReadDataPacket(ids={}, '
                'address={}, length={})'.format(self.parameters[2:],
                                                self.parameters[0],
                                                self.parameters[1]))


class DxlWriteDataPacket(DxlInstructionPacket):
    """ This class is used to reprensent write data packet (to write value). """
    def __new__(cls, id, address, coded_value):
        return DxlInstructionPacket.__new__(cls, id,
                                            DxlInstruction.WRITE_DATA,
                                            tuple(itertools.chain((address,),
                                                                  coded_value)))

    def __repr__(self):
        return ('DxlWriteDataPacket(id={}, '
                'address={}, value={})'.format(self.id,
                                               self.parameters[0],
                                               self.parameters[1:]))


class DxlSyncWritePacket(DxlInstructionPacket):
    """ This class is used to represent sync write packet (to synchronously write values). """
    def __new__(cls, address, length, id_value_couples):
        return DxlInstructionPacket.__new__(cls, DxlBroadcast,
                                            DxlInstruction.SYNC_WRITE,
                                            tuple(itertools.chain((address, length),
                                                                  id_value_couples)))

    def __repr__(self):
        address = self.parameters[0]
        length = self.parameters[1]

        a = numpy.array(self.parameters[2:]).reshape((-1, length + 1))
        ids = a[:, 0]
        values = [tuple(v) for v in a[:, 1:]]

        return ('DxlSyncWriteDataPacket(ids={}, '
                'address={}, length={}, values={})'.format(ids,
                                                           address,
                                                           length,
                                                           values))


# MARK: - Status Packet
class DxlStatusPacket(namedtuple('DxlStatusPacket', ('id', 'error', 'parameters'))):
    """ This class is used to represent a dynamixel status packet.

        A status packet is constructed as follows:
        [0xFF, 0xFF, ID, LENGTH, ERROR, PARAM 1, PARAM 2, ..., PARAM N, CHECKSUM]

        (for more details see http://support.robotis.com/en/product/dxl_main.htm)

        """
    @classmethod
    def from_string(cls, data):
        packet = bytearray(data)

        header = DxlPacketHeader.from_string(packet[:4])

        if len(packet) != DxlPacketHeader.length + header.packet_length \
                or cls._checksum(packet) != packet[-1]:
            raise ValueError('try to parse corrupted data ({})'.format(packet))

        return cls(header.id, packet[4], tuple(packet[5:-1]))

    @classmethod
    def _checksum(cls, packet):
        return int(255 - (sum(packet[2:-1]) % 256))

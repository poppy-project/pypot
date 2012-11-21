# -*- coding: utf-8 -*-

import array
import itertools

from collections import namedtuple


DynamixelBroadcast = 254

class DynamixelInstruction(object):
    PING = 0x01
    READ_DATA = 0x02
    WRITE_DATA = 0x03
    SYNC_WRITE = 0x83
    SYNC_READ = 0x84


# MARK: - Packet Header

class DynamixelPacketHeader(namedtuple('DynamixelPacketHeader', ('id', 'packet_length'))):
    """ This class represents the header of a Dynamixel Packet.
        
        They are constructed as follows [0xFF, 0xFF, ID, LENGTH] where :
            * ID represents the ID of the motor who received (resp. sent) the intruction (resp. status) packet.
            * LENGTH represents the length of the rest of the packet
        
        """
    length = 4
    marker = array.array('B', (0xFF, 0xFF))
    
    @classmethod
    def from_string(cls, data):
        header = array.array('B', data)
        
        if len(header) != cls.length or header[:len(cls.marker)] != cls.marker:
            raise ValueError('try to parse corrupted data ({})'.format(header))
        
        return cls(header[2], header[3])


# MARK: - Instruction Packet

class DynamixelInstructionPacket(namedtuple('DynamixelInstructionPacket', ('id', 'instruction', 'parameters'))):
    """ This class is used to represent a dynamixel instruction packet.
        
        An instruction packet is constructed as follows:
        [0xFF, 0xFF, ID, LENGTH, INSTRUCTION, PARAM 1, PARAM 2, ..., PARAM N, CHECKSUM]
        
        (for more details see http://support.robotis.com/en/product/dxl_main.htm)
        
        """
    def to_array(self):
        return array.array('B',
                           itertools.chain(DynamixelPacketHeader.marker,
                                           (self.id, self.length, self.instruction),
                                           self.parameters,
                                           (self.checksum, )))
    
    def to_string(self):
        return self.to_array().tostring()
    
    @property
    def length(self):
        return len(self.parameters) + 2
    
    @property
    def checksum(self):
        return int(255 - ((self.id + self.length + self.instruction + sum(self.parameters)) % 256))


class DynamixelPingPacket(DynamixelInstructionPacket):
    """ This class is used to represent ping packet. """
    def __new__(cls, id):
        return DynamixelInstructionPacket.__new__(cls, id, DynamixelInstruction.PING, ())

class DynamixelReadDataPacket(DynamixelInstructionPacket):
    """ This class is used to represent read data packet (to read value). """
    def __new__(cls, id, address, length):
        return DynamixelInstructionPacket.__new__(cls, id,
                                                  DynamixelInstruction.READ_DATA,
                                                  (address, length))

class DynamixelSyncReadPacket(DynamixelInstructionPacket):
    """ This class is used to represent sync read packet (to synchronously read values). """
    def __new__(cls, ids, address, length):
        return DynamixelInstructionPacket.__new__(cls, DynamixelBroadcast,
                                                  DynamixelInstruction.SYNC_READ,
                                                  tuple(itertools.chain((address, length), ids)))

class DynamixelWriteDataPacket(DynamixelInstructionPacket):
    """ This class is used to reprensent write data packet (to write value). """
    def __new__(cls, id, address, coded_value):
        return DynamixelInstructionPacket.__new__(cls, id,
                                                  DynamixelInstruction.WRITE_DATA,
                                                  tuple(itertools.chain((address,), coded_value)))

class DynamixelSyncWritePacket(DynamixelInstructionPacket):
    """ This class is used to represent sync write packet (to synchronously write values). """
    def __new__(cls, address, length, id_value_couples):
        return DynamixelInstructionPacket.__new__(cls, DynamixelBroadcast,
                                                  DynamixelInstruction.SYNC_WRITE,
                                                  tuple(itertools.chain((address, length), id_value_couples)))


# MARK: - Status Packet

class DynamixelStatusPacket(namedtuple('DynamixelStatusPacket', ('id', 'error', 'parameters'))):
    """ This class is used to represent a dynamixel status packet.
        
        A status packet is constructed as follows:
        [0xFF, 0xFF, ID, LENGTH, ERROR, PARAM 1, PARAM 2, ..., PARAM N, CHECKSUM]
        
        (for more details see http://support.robotis.com/en/product/dxl_main.htm)
        
        """
    @classmethod
    def from_string(cls, data):
        packet = array.array('B', data)
        
        header = DynamixelPacketHeader.from_string(packet[:4])
        
        if len(packet) != DynamixelPacketHeader.length + header.packet_length \
            or cls._checksum(packet) != packet[-1]:
            raise ValueError('try to parse corrupted data ({})'.format(packet))
        
        return cls(header.id, packet[4], tuple(packet[5:-1]))
    
    @classmethod
    def _checksum(cls, packet):
        return int(255 - (sum(packet[2:-1]) % 256))


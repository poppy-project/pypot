import numpy
import itertools

from collections import namedtuple

from ..conversion import dxl_code, dxl_decode

name = 'v2'

DxlBroadcast = 254


class DxlInstruction(object):
    PING = 0x01
    READ_DATA = 0x02
    WRITE_DATA = 0x03
    RESET = 0x06
    SYNC_READ = 0x82
    SYNC_WRITE = 0x83


# MARK: - Packet Header

class DxlPacketHeader(namedtuple('DxlPacketHeader', ('id', 'packet_length'))):
    """ This class represents the header of a Dxl Packet.

        They are constructed as follows [0xFF, 0xFF, 0xFD, 0x00, ID, LEN_L, LEN_H] where:
            * ID represents the ID of the motor who received (resp. sent) the intruction (resp. status) packet.
            * LEN_L, LEN_H represents the length of the rest of the packet

        """
    length = 7
    marker = bytearray((0xFF, 0xFF, 0xFD, 0x00))

    @classmethod
    def from_string(cls, data):
        header = bytearray(data)

        if len(header) != cls.length or header[:len(cls.marker)] != cls.marker:
            raise ValueError('try to parse corrupted data ({})'.format(header))

        return cls(header[4], dxl_decode((header[5], header[6])))


# MARK: - Instruction Packet

class DxlInstructionPacket(namedtuple('DxlInstructionPacket',
                                      ('id', 'instruction', 'parameters'))):
    """ This class is used to represent a dynamixel instruction packet.

        An instruction packet is constructed as follows:
        [0xFF, 0xFF, 0xFD, 0x00, ID, LEN_L, LEN_H, INST, PARAM 1, PARAM 2, ..., PARAM N, CRC_L, CRC_H]

        (for more details see http://support.robotis.com/en/product/dxl_main.htm)

        """
    def _buff(self):
        return bytearray(itertools.chain(DxlPacketHeader.marker,
                                         (self.id, ),
                                         dxl_code(self.length, 2),
                                         (self.instruction, ),
                                         self.parameters))

    def to_array(self):
        return self._buff() + bytearray(dxl_code(self.checksum, 2))

    def to_string(self):
        return bytes(self.to_array())

    @property
    def length(self):
        return len(self.parameters) + 3

    @property
    def checksum(self):
        return crc16(self._buff(), 5 + self.length)


class DxlPingPacket(DxlInstructionPacket):
    """ This class is used to represent ping packet. """
    def __new__(cls, id):
        return DxlInstructionPacket.__new__(cls, id, DxlInstruction.PING, ())

    def __repr__(self):
        return 'DxlPingPacket(id={})'.format(self.id)


class DxlResetPacket(DxlInstructionPacket):
    """ This class is used to represent factory reset packet. """
    def __new__(cls, id, mode):
        return DxlInstructionPacket.__new__(cls, id,
                                            DxlInstruction.RESET, (mode, ))


class DxlReadDataPacket(DxlInstructionPacket):
    """ This class is used to represent read data packet (to read value). """
    def __new__(cls, id, address, length):
        return DxlInstructionPacket.__new__(cls, id,
                                            DxlInstruction.READ_DATA,
                                            list(dxl_code(address, 2)) +
                                            list(dxl_code(length, 2)))

    def __repr__(self):
        return 'DxlReadDataPacket(id={}, address={}, length={})'.format(
            self.id,
            dxl_decode(list(reversed(self.parameters[0:2]))),
            dxl_decode(list(reversed(self.parameters[2:4]))))


class DxlSyncReadPacket(DxlInstructionPacket):
    """ This class is used to represent sync read packet (to synchronously read values). """
    def __new__(cls, ids, address, length):
        return DxlInstructionPacket.__new__(cls, DxlBroadcast,
                                            DxlInstruction.SYNC_READ,
                                            list(dxl_code(address, 2)) +
                                            list(dxl_code(length, 2)) +
                                            list(ids))

    def __repr__(self):
        return ('DxlSyncReadDataPacket(ids={}, '
                'address={}, length={})'.format(self.parameters[4:],
                                                dxl_decode(self.parameters[0:2]),
                                                dxl_decode(self.parameters[2:4])))


class DxlWriteDataPacket(DxlInstructionPacket):
    """ This class is used to reprensent write data packet (to write value). """
    def __new__(cls, id, address, coded_value):
        return DxlInstructionPacket.__new__(cls, id,
                                            DxlInstruction.WRITE_DATA,
                                            list(dxl_code(address, 2)) +
                                            list(coded_value))

    def __repr__(self):
        return ('DxlWriteDataPacket(id={}, address={}, value={})'.format(
                self.id,
                dxl_decode(self.parameters[0:2]),
                tuple(self.parameters[2:])))


class DxlSyncWritePacket(DxlInstructionPacket):
    """ This class is used to represent sync write packet (to synchronously write values). """
    def __new__(cls, address, length, id_value_couples):
        return DxlInstructionPacket.__new__(cls, DxlBroadcast,
                                            DxlInstruction.SYNC_WRITE,
                                            list(itertools.chain(dxl_code(address, 2),
                                                                 dxl_code(length, 2),
                                                                 id_value_couples)))

    def __repr__(self):
        address = dxl_decode(self.parameters[0:2])
        length = dxl_decode(self.parameters[2:4])

        a = numpy.array(self.parameters[4:]).reshape((-1, length + 1))
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
        [0xFF, 0xFF, 0xFD, 0x00, ID, LEN_L, LEN_H, 0x55, ERROR, PARAM 1, PARAM 2, ..., PARAM N, CRC_L, CRC_H]

        (for more details see http://support.robotis.com/en/product/dxl_main.htm)

        """
    @classmethod
    def from_string(cls, data):
        packet = bytearray(data)

        header = DxlPacketHeader.from_string(packet[:DxlPacketHeader.length])

        if (len(packet) != DxlPacketHeader.length + header.packet_length or
                cls._checksum(packet) != packet[-2:]):
            raise ValueError('try to parse corrupted data ({})'.format(packet))

        return cls(header.id, packet[8], tuple(packet[9:-2]))

    @classmethod
    def _checksum(cls, packet):
        return bytearray(dxl_code(crc16(packet[:-2], len(packet) - 2), 2))


def crc16(data_blk, data_blk_size, crc_accum=0):
    for j in range(data_blk_size):
        i = ((crc_accum >> 8) ^ data_blk[j]) & 0xFF
        crc_accum = ((crc_accum << 8) ^ crc_table[i]) % (2 ** 16)

    return crc_accum

crc_table = [
    0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
    0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
    0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
    0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
    0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
    0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
    0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
    0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
    0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192,
    0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
    0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
    0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
    0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
    0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
    0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
    0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
    0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
    0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
    0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
    0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
    0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
    0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
    0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
    0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
    0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
    0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
    0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
    0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
    0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
    0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
    0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
    0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202
]

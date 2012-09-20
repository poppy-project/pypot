import array

from pypot.dynamixel.protocol import *

# MARK: - Generic Packet

class DynamixelPacketHeader(object):
    """
        This class represents the header of a Dynamixel Packet.
        
        The header of all Dynamixel packets (instruction or status) are
        constructed as follows: [OxFF, OxFF, ID, LENGTH].
        
            * In the case of an instruction packet:
                * ID: It is the ID of the Dynamixel motor which will receive the packet.
                * LENGTH: It is the length of the instruction packet.
            * In the case of a status packet:
                * ID: It is the ID of the motor which sent the status packet.
                * LENGTH: It is the length of the status packet.
        
        """
    LENGTH = 4
    
    def __init__(self, motor_id, packet_length):
        self.motor_id = motor_id
        self.packet_length = packet_length
    
    def to_bytes(self):
        """ Transforms the header into bytes suitable for serial communication. """
        return array.array('B', [0xFF, 0xFF, self.motor_id, self.packet_length]).tostring()
    
    @classmethod
    def from_bytes(cls, bytes):
        """
            Creates a new header instance from bytes.
            
            :param string bytes: a raw header string
            :raises: DynamixelInconsistentPacketError if the given bytes do not correspond to a standard dynamixel packet header.
            
            """
        header = list(bytes)
        
        if header[:2] != ['\xff', '\xff'] or len(header) != DynamixelPacketHeader.LENGTH:
            raise DynamixelInconsistentPacketError('Inconsistent header', bytes)
        
        motor_id, length = map(ord, header[2:])
        return cls(motor_id, length)


class DynamixelPacket(object):
    """ Generic class for all the Dynamixel communication packet. """
    
    def __init__(self, motor_id, parameters=()):
        self.motor_id = motor_id
        self.length = len(parameters) + 2
        self.parameters = list(parameters)
        
        self.header = DynamixelPacketHeader(self.motor_id, self.length)
    
    def __repr__(self):
        return str(map(ord, self.to_bytes()))
    
    def __len__(self):
        return len(self.to_bytes())
    
    def to_bytes(self):
        raise NotImplementedError

# MARK: - Instruction Packet

class DynamixelInstructionPacket(DynamixelPacket):
    """
        This class is used to represent a dynamixel instruction packet.
        
        It is based on the DynamixelPacket class.
        
        A Dynamixel instruction packet is represented as follows:
        [0xFF, 0xFF, ID, LENGTH, INSTRUCTION, PARAM 1, PARAM 2, ..., PARAM N, CHECKSUM]
        where each element is coded on a single byte.
        
        The ID is the id of the motor which will receive the instruction packet.
        The length corresponds to the length of the instruction packet (i.e. the
        number of parameters + 2).
        
        The INSTRUCTION could be one of the following:
        ['PING', 'READ_DATA', 'WRITE_DATA', 'SYNC_READ', 'SYNC_WRITE']
        (the other instructions have not been implemented so far).
        
        The PARAMETERS are used when the instruction needs other data (e.g. the
        address of the data to read).
        
        The CHECKSUM is used to check if any communication error has occured.
        
        (for more details, see
        http://support.robotis.com/en/product/dynamixel/communication/dxl_packet.htm)
        
        """
    def __init__(self, motor_id, instruction_name, parameters=()):
        DynamixelPacket.__init__(self, motor_id, parameters)
        
        self.instruction = DXL_INSTRUCTIONS[instruction_name]
        self.checksum = self._compute_checksum()
    
    def _compute_checksum(self):
        # Check Sum = ~(ID + Length + Instruction + Parameter1 + ... + Parameter N)
        return 255 - ((self.motor_id + self.length + self.instruction + sum(self.parameters)) % 256)
    
    def to_bytes(self):
        return self.header.to_bytes() + \
            array.array('B', [self.instruction] + self.parameters + [self.checksum]).tostring()


class DynamixelPingPacket(DynamixelInstructionPacket):
    """ This class allows the creation of ping packets. """
    
    def __init__(self, motor_id):
        """
            Creates a PING packet.
            
            A PING packet is constructed as follows:
            [0xFF, 0xFF, ID, 2, 0x01, CHECKSUM]
            
            :param int motor_id: motor id [0-253]
            
            """
        DynamixelInstructionPacket.__init__(self,
                                            motor_id,
                                            'PING')

class DynamixelReadDataPacket(DynamixelInstructionPacket):
    """ This class allows the creation of READ_DATA packets. """
    
    def __init__(self, motor_id, control_name):
        """
            Creates a new READ_DATA packet.
            
            A READ_DATA packet is constructed as follows:
            [0xFF, 0xFF, ID, 4, 0x02, ADDRESS, LENGTH_OF_DATA, CHECKSUM]
            
            :param int motor_id: motor id [0-253]
            :param string control_name: The name of the control to read must be provided. It must correspond to one of the values provided by the DXL_CONTROLS dictionary presents in the :py:mod:`~/pypot.dynamixel.protocol` file.
            
            """
        parameters = (REG_ADDRESS(control_name), REG_LENGTH(control_name))
        
        DynamixelInstructionPacket.__init__(self,
                                            motor_id,
                                            'READ_DATA',
                                            parameters)

class DynamixelSyncReadDataPacket(DynamixelInstructionPacket):
    """
        This class allows the creation of SYNC_READ packets.
        
        The name of the control to read must be provided. It must correspond to
        one of the values provided by the DXL_CONTROLS dictionary presents in the
        protocol.py file.
        
        Instead of providing a motor id, you can here provide a list of motor ids.
        
        .. note:: SYNC_READ packets only works with the USB2AX controller.
        
        """
    def __init__(self, motor_ids, control_name):
        """
            Creates a new SYNC_READ packet.
            
            A SYNC_READ packet is constructed as follows:
            [0xFF, 0xFF, BROADCAST, LEN(MOTORS) + 4, 0x84, ADDRESS, LENGTH_OF_DATA,
            ID 1, ID 2, ..., ID N, CHECKSUM]

            :param motor_ids: motor ids [0-253]
            :type motor_ids: list of int
            :param string control_name: The name of the control to read must be provided. It must correspond to one of the values provided by the DXL_CONTROLS dictionary presents in the :py:mod:`~pypot.dynamixel.protocol` file.
            
            """
        parameters = [REG_ADDRESS(control_name), REG_LENGTH(control_name)] + list(motor_ids)
        
        DynamixelInstructionPacket.__init__(self,
                                            DXL_BROADCAST,
                                            'SYNC_READ',
                                            parameters)

class DynamixelWriteDataPacket(DynamixelInstructionPacket):
    """
        This class allows the creation of WRITE_DATA packet.
        
        The name of the control to write must be provided. It must correspond to
        one of the values provided by the DXL_CONTROLS dictionary presents in the
        :py:mod:`~pypot.dynamixel.protocol` file.
        
        The data to write must also be provided and match the required data length.
        
        """
    def __init__(self, motor_id, control_name, data):
        """
            Creates a new WRITE_DATA packet.
            
            A WRITE_DATA packet is constructed as follows:
            [0xFF, 0xFF, ID, LEN(DATA) + 3, 0x03, ADDRESS, DATA, CHECKSUM]
            
            :param int motor_id: motor id [0-253]
            :param string control_name: The name of the control to read must be provided. It must correspond to one of the values provided by the DXL_CONTROLS dictionary presents in the :py:mod:`~pypot.dynamixel.protocol` file.
            :param data: data to write, the length of the data must match the control length
            :type data: list of int
            
            """
        parameters = [REG_ADDRESS(control_name)] + list(data)
        
        if len(data) != REG_LENGTH(control_name):
            raise ValueError('Inconsistent data (%s) for the control %s' \
                             % (data, control_name))
        
        DynamixelInstructionPacket.__init__(self,
                                            motor_id,
                                            'WRITE_DATA',
                                            parameters)

class DynamixelSyncWriteDataPacket(DynamixelInstructionPacket):
    """
        This class allows the creation of SYNC_WRITE packets.
        
        The name of the control to read must be provided. It must correspond to
        one of the values provided by the DXL_CONTROLS dictionary presents in the
        :py:mod:`~pypot.dynamixel.protocol` file.
        
        Instead of providing a motor id, you can here provide a list of motor ids.
        
        The data to write must also be provided and match the required data length.
        
        """
    def __init__(self, control_name, data):
        """
            Creates a new SYNC_WRITE packet.
            
            A SYNC_WRITE packet is constructed as follows:
            [0xFF, 0xFF, BROADCAST, LENGTH + 4, 0x83, ADDRESS, DATA_LENGTH,
            ID 1, DATA 1, DATA 2, ...,
            ID 2, DATA 1, DATA 2, ...,
            ....,
            ID N, DATA 1, DATA 2, ...,
            CHECKSUM]
            
            :param string control_name: The name of the control to read must be provided. It must correspond to one of the values provided by the DXL_CONTROLS dictionary presents in the :py:mod:`~pypot.dynamixel.protocol` file.
            :param data: data to be written. The length of the data must match the control length * the number of motors. The motor ids are directly given in the data for convenience.
            :type data: list of (id, data 1, data 2, ..., data N)
            
            """
        # TODO: verifier la taille des donnees envoyees
        
        parameters = [REG_ADDRESS(control_name), REG_LENGTH(control_name)] + list(data)
        
        DynamixelInstructionPacket.__init__(self,
                                            DXL_BROADCAST,
                                            'SYNC_WRITE',
                                            parameters)

# MARK: - Status Packet

class DynamixelStatusPacket(DynamixelPacket):
    """
        This class is used to represent a dynamixel status packet.
        
        It is based on the DynamixelPacket class.
        
        A Dynamixel status packet is represented as follows:
        [0xFF, 0xFF, ID, LENGTH, ERROR, PARAM 1, PARAM 2, ..., PARAM N, CHECKSUM]
        where each element is coded on a single byte.
        
        The ID is the id of the motor which has sent the status packet.
        The length corresponds to the length of the status packet (i.e. the
        number of parameters + 2).
        
        The ERROR codes different status error that could occur during communication
        with a dynamixel motor (see http://support.robotis.com/en/product/dynamixel/communication/dxl_packet.htm for details).
        
        The PARAMETERS are used to return other data (e.g. the read data).
        
        The CHECKSUM is used to check if any communication error has occured.
        
        (for more details, see
        http://support.robotis.com/en/product/dynamixel/communication/dxl_packet.htm)
        
        """
    def __init__(self, motor_id, error, parameters):
        DynamixelPacket.__init__(self, motor_id, parameters)
        
        self.error = error
        self.checksum = self._compute_checksum()
    
    @classmethod
    def from_bytes(cls, bytes):
        header = DynamixelPacketHeader.from_bytes(bytes[:4])
        
        data = map(ord, list(bytes)[4:])
        
        error = data[0]
        parameters = data[1:-1]
        checksum = data[-1]
        
        if header.packet_length != len(parameters) + 2:
            raise DynamixelInconsistentPacketError('Packet received with an inconsistent length', bytes)
        
        status_packet = cls(header.motor_id, error, parameters)
        
        if status_packet.checksum != checksum:
            raise DynamixelInconsistentPacketError('Packet received with a wrong checksum', bytes)
        
        return status_packet
    
                
    def to_bytes(self):
        return self.header.to_bytes() + \
            array.array('B', [self.error] + self.parameters + [self.checksum]).tostring()

    
    
    def _compute_checksum(self):
        return 255 - ((self.motor_id + self.length + self.error + sum(self.parameters)) % 256)

# MARK: - Packet Error

class DynamixelInconsistentPacketError(Exception):
    def __init__(self, message, bytes):
        self.message = message
        self.packet = map(ord, bytes)
    
    def __str__(self):
        return '%s (%s)' % (self.message, self.packet)
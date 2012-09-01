# coding=utf-8

import array
import serial
import threading

from pypot.utils import flatten_list, reshape_list
from conversions import *
from protocol import *


class DynamixelIO:
    """
        This class handles the low-level communication with robotis motors.
        
        Using a USB communication device such as USB2DYNAMIXEL or USB2AX,
        you can open serial communication with robotis motors (MX, RX, AX)
        using communication protocols TTL or RS485.
        
        This class handles low-level IO communication by automatically creating
        packets based on the need to access the different registers in the motors.
        Users can use high-level access such as position, load, torque to control
        the motors.
        
        Methods
        -------
        
        For a complete list of all available methods use introspection.
        
        Discovering motors:
        ping
        scan
        
        Controlling individual motors (get/set):
        angle_limits
        max_torque
        torque_enabled
        pid
        compliance_margins / compliance_slopes
        position
        speed
        torque
        load
        
        Controlling groups of motors (sync):
        position
        speed
        torque
        load
        
        Exceptions
        ----------
        
        DynamixelCommunicationError:
        raised when the serial communication failed
        
        DynamixelUnsupportedFunctionForMotorError:
        raised when calling a method that is unsupported by the motor model
        
        DynamixelMotorError:
        raised when a motor returns an error code
        
        """
    
    __open_ports = []
    
    
    def __init__(self, port, baudrate=1000000, timeout=1.0):
        """
            Opens the serial port and sets the communication parameters.
            
            The port can only be accessed by a single DynamixelIO.
            
            Parameters
            ----------
            port : string
            (e.g. Unix (/dev/tty...), Windows (COM...))
            
            baudrate : int (optional)
            default for new motors : 57600
            for PyPot motors : 1000000
            
            timeout : float (optional)
            read timeout in seconds
            
            """
        if port in self.__open_ports:
            raise ValueError('Port already used (%s)!' % (port))
        
        self._serial = serial.Serial(port, baudrate, timeout=timeout)
        self.__open_ports.append(port)
        
        self._lock = threading.RLock()
        
        self._motor_models = {}
    
    def __del__(self):
        """ Automatically closes the serial communication on destruction. """
        self.__open_ports.remove(self._serial.port)
        self._serial.close()
    
    def __repr__(self):
        return "<DXL IO: port='%s' baudrate=%d timeout=%.g>" % (self._serial.port,
                                                                self._serial.baudrate,
                                                                self._serial.timeout)
    
    
    def flush_serial_communication(self):
        """
            Flush the serial communication.
            
            Use this method after a communication issue (such as a timeout) to
            refresh the communication bus.
            
            """
        self._serial.flushInput()
        self._serial.flushOutput()
    
    
    # MARK: - Motor discovery
    
    def ping(self, motor_id):
        """
            Pings the motor with the specified id.
            
            Parameters
            ----------
            motor_id : int
            The motor ID [0-253]
            
            Returns
            -------
            bool
            
            """
        if not (0 <= motor_id <= 253):
            raise ValueError('Motor id must be in [0, 253]!')
        
        ping_packet = self._build_packet(motor_id, 'PING')
        
        try:
            self._send_packet(ping_packet)
            return True
        
        except DynamixelTimeoutError:
            return False
    
    
    def scan(self, possible_ids=range(254)):
        """
            Finds the ids of all the motors connected to the bus.
            
            Parameters
            ----------
            possible_ids : list (optional)
            Specify the range of ids to search
            
            Returns
            -------
            list : found motor ids
            
            """
        return filter(self.ping, possible_ids)
    
    
    def get_model(self, motor_id):
        """
            Finds the model name of the robotis motor.
            
            Parameters
            ----------
            motor_id : int
            The motor ID [0-253]
            
            Returns
            -------
            one of the DXL_MODEL_NUMBER values (see protocol.py)
            
            """
        model_number = self._send_read_packet(motor_id, 'MODEL_NUMBER')
        
        if not DXL_MODEL_NUMBER.has_key(model_number):
            raise DynamixelUnsupportedMotorError(motor_id, model_number)
        
        motor_model = DXL_MODEL_NUMBER[model_number]
        self._motor_models[motor_id] = motor_model
        return motor_model
    
    # def specify_model(self, motor_id, motor_model):
    #     """
    #         Specify the model of a virtual motor.
    
    #         Parameters
    #         ----------
    #         :param motor_id: int
    #             The motor ID [0-253]
    
    #         """
    #     if motor_model not in DXL_MODEL_NUMBER.values():
    #         raise ValueError('Unknown motor model: %s' % (motor_model))
    
    #     self._motor_models[motor_id] = motor_model
    
    def _lazy_get_model(self, motor_id):
        """ Finds the motor model if it is not already known. """
        if not self._motor_models.has_key(motor_id):
            self.get_model(motor_id)
        
        return self._motor_models[motor_id]
    
    
    # MARK: - Sync Read/Write
    
    def get_sync_positions(self, motor_ids):
        """
            Synchronizes the getting of positions in degrees of all motors specified.
            
            : warn This method only works with the USB2AX.
            
            Parameters
            ----------
            motor_id : list<int>
            
            Returns
            -------
            list of position in degrees
            
            """
        motor_models = [self._lazy_get_model(mid) for mid in motor_ids]
        motor_positions = self._send_sync_read_packet(motor_ids, 'PRESENT_POSITION')
        
        return [position_to_degree(pos, model) for model, pos in zip(motor_models, motor_positions)]
    
    def set_sync_positions(self, id_pos_pairs):
        """
            Synchronizes the setting of the specified positions (in degrees) to the motors.
            
            Parameters
            ----------
            id_pos_pairs : list<motor_id, degree>
            
            """
        ids, degrees = zip(*id_pos_pairs)
        motor_models = [self._lazy_get_model(mid) for mid in ids]
        positions = [degree_to_position(rad, model) for rad, model in zip(degrees, motor_models)]
        
        self._send_sync_write_packet('GOAL_POSITION', zip(ids, positions))
    
    
    def get_sync_speeds(self, motor_ids):
        """
            Synchronizes the getting of speeds of all motors specified.
            
            : warn This method only works with the USB2AX.
            
            Parameters
            ----------
            motor_id : list<int>
            
            Returns
            -------
            list of speed in rpm (positive values correspond to clockwise)
            
            """
        return map(speed_to_rpm,
                   self._send_sync_read_packet(motor_ids, 'PRESENT_SPEED'))
    
    def set_sync_speeds(self, id_speed_pairs):
        """
            Synchronizes the setting of the specified speeds to the specified motors.
            
            Parameters
            ----------
            id_speed_pairs : list<motor_id, rpm>
            
            """
        ids, speeds = zip(*id_speed_pairs)
        speeds = map(rpm_to_speed, speeds)
        self._send_sync_write_packet('MOVING_SPEED', zip(ids, speeds))
    
    
    def get_sync_loads(self, motor_ids):
        """
            Synchronizes the getting of internal loads of all motors specified.
            
            : warn This method only works with the USB2AX.
            
            Parameters
            ----------
            motor_id : list<int>
            
            Returns
            -------
            list of load
            
            """
        return map(load_to_percent,
                   self._send_sync_read_packet(motor_ids, 'PRESENT_LOAD'))
    
    def set_sync_torque_limits(self, id_torque_pairs):
        """
            Synchronizes the setting of the specified torque limits to the specified motors.
            
            Parameters
            ----------
            id_speed_pairs : list<motor_id, torque limit>
            The torque limit is a percentage of the max torque.
            
            """
        ids, torques = zip(*id_torque_pairs)
        torques = map(percent_to_torque_limit, torques)
        
        self._send_sync_write_packet('TORQUE_LIMIT', zip(ids, torques))
    
    
    def get_sync_positions_speeds_loads(self, motor_ids):
        """
            Synchronizes the getting of positions, speeds, loads of all motors specified.
            
            : warn This method only works with the USB2AX.
            
            Parameters
            ----------
            motor_id : list<int>
            
            Returns
            -------
            list of (position, speed, load)
            
            """
        motor_models = [self._lazy_get_model(mid) for mid in motor_ids]
        
        pos, speed, load = zip(*self._send_sync_read_packet(motor_ids, 'PRESENT_POS_SPEED_LOAD'))
        
        pos = [position_to_degree(pos, model) for pos, model in zip(pos, motor_models)]
        speed = map(speed_to_rpm, speed)
        load = map(load_to_percent, load)
        
        return zip(pos, speed, load)
    
    def set_sync_positions_speeds_torque_limits(self, id_pos_speed_torque_tuples):
        """
            Synchronizes the setting of the specified positions, speeds and torque limits to the motors.
            
            Parameters
            ----------
            id_speed_pairs : list<motor_id, position, speed, torque limit>
            
            """
        motor_models = [self._lazy_get_model(mid) for mid in motor_ids]
        
        ids, pos, speed, torque = zip(*id_pos_speed_torque_tuples)
        
        pos = [degree_to_position(rad, model) for rad, model in zip(pos, motor_models)]
        speed = map(rpm_to_speed, speed)
        torque = map(percent_to_torque_limit, torque)
        
        self._send_sync_write_packet('GOAL_POS_SPEED_TORQUE', zip(ids, pos, speed, torque))
    
    
    
    # MARK: - Dxl Motor EEPROM Access
    # Those values should not be modified too often !!!
    
    def change_id(self, motor_id, new_motor_id):
        """
            Changes the id of the motor.
            
            Each motor must have a unique id on the bus.
            The range of possible ids is [0, 253].
            
            Parameters
            ----------
            motor_id : int
            current motor id
            new_motor_id : int
            new motor id
            
            Exceptions
            ----------
            ValueError : Raised when the id is already taken
            
            """
        if self.ping(new_motor_id):
            raise ValueError('id %d already used' % (new_motor_id))
        
        self._send_write_packet(motor_id, 'ID', new_motor_id)
    
    
    def set_baudrate(self, motor_id, baudrate):
        """
            Changes the baudrate of a specified motor.
            
            :warn the baudrate of the motor must match the baudrate of the
            port. When the baurate is changed for the motor, it will be necessary to
            open a new port with the new baurate to re-establish communication.
            
            Parameters
            ----------
            motor_id : int
            the specified motor
            baurate : int
            see http://support.robotis.com/en/product/dxl_main.htm for possible values
            
            """
        self._send_write_packet(motor_id, 'BAUDRATE', baudrate)
    
    
    def get_return_delay_time(self, motor_id):
        """ Returns the current delay time in µs. """
        return self._send_read_packet(motor_id, 'RETURN_DELAY_TIME') * 2
    
    def set_return_delay_time(self, motor_id, return_delay_time):
        """
            Sets a new return delay time in µs (the value must be in [0, 508]).
            
            This delay is the time the motor waits to return the status packet.
            For optimal performance set this to 0µs.
            
            """
        if not (0 <= return_delay_time <= 508):
            raise ValueError('the return delay time must be in [0, 508]')
        
        self._send_write_packet(motor_id, 'RETURN_DELAY_TIME', int(return_delay_time / 2))
    
    
    def get_angle_limits(self, motor_id):
        """
            Gets the lower and upper angle limits of the motor.
            
            Returns
            -------
            (lower_limit, upper_limit) : tuple
            The limits are in degrees.
            
            """
        return map(lambda pos: position_to_degree(pos, self._lazy_get_model(motor_id)),
                   self._send_read_packet(motor_id, 'ANGLE_LIMITS'))
    
    def set_angle_limits(self, motor_id,
                         lower_limit, upper_limit):
        """
            Sets the lower and upper angle limits of the motor.
            
            These values are written to the EEPROM and therefore conserved
            after cycling the power.
            
            Parameters
            ----------
            lower_limit : float
            upper_limit : float
            
            The limits are in degrees.
            The hardware upper limit depends on the motor model.
            MX : [0, 2 * PI]
            AX, RX : [0, 5/3 * PI]
            
            """
        if lower_limit >= upper_limit:
            raise ValueError('The lower limit (%d) must be less than the upper limit (%d).'
                             % (lower_limit, upper_limit))
        
        self._send_write_packet(motor_id,
                                'ANGLE_LIMITS',
                                map(lambda rad: degree_to_position(rad, self._lazy_get_model(motor_id)),
                                    (lower_limit, upper_limit)))
    
    
    # def get_drive_mode(self, motor_id):
    #     motor_model = self._lazy_get_model(motor_id)
    #     if not motor_model.startswith('EX'):
    #         raise DynamixelUnsupportedFunctionForMotorError(self.get_drive_mode,
    #                                                         motor_id,
    #                                                         motor_model)
    
    #     return self._send_read_packet(motor_id, 'DRIVE_MODE')
    
    # def set_drive_mode(self, motor_id, drive_mode):
    #     motor_model = self._lazy_get_model(motor_id)
    #     if not motor_model.startswith('EX'):
    #         raise DynamixelUnsupportedFunctionForMotorError(self.set_drive_mode,
    #                                                         motor_id,
    #                                                         motor_model)
    
    #     self._send_write_packet(motor_id, 'DRIVE_MODE', int(drive_mode))
    
    
    def get_limit_temperature(self, motor_id):
        """
            Returns the motor highest limit of operating temperature (in Celsius).
            
            If the internal temperature of a motor exceeds this limit, it sets
            the Over Heating Error Bit of Status Packet to True and triggers an
            alarm (LED and shutdown).
            
            """
        return self._send_read_packet(motor_id, 'HIGHEST_LIMIT_TEMPERATURE')
    
    def set_limit_temperature(self, motor_id, limit_temperature):
        """
            Sets the highest limit of operating temperature.
            
            : warn Do not set the temperature lower/higher than the default value.
            Using the motor when the temperature is high may and can cause damage.
            
            Parameters
            ----------
            motor_id : int
            The motor ID [0-253]
            limit_temperature : int
            Celcius degrees in range [10-99]
            """
        if not (10 <= limit_temperature <= 99):
            raise ValueError('The temperature limit must be in [10,99]')
        
        self._send_write_packet(motor_id, 'HIGHEST_LIMIT_TEMPERATURE', limit_temperature)
    
    
    def get_voltage_limits(self, motor_id):
        """
            Returns the operation range of voltage (V).
            
            If present voltage is out of the range, Voltage Range Error
            of Status Packet is returned as '1' and Alarm is triggered as set
            in the Alarm LED and Alarm Shutdown.
            """
        return map(lambda v: v * 0.1,
                   self._send_read_packet(motor_id, 'VOLTAGE_LIMITS'))
    
    def set_voltage_limits(self, motor_id,
                           lowest_limit_voltage, highest_limit_voltage):
        """
            Sets the operation voltage range for the motor.
            
            If Present Voltage is out of the range, Voltage Range Error
            of Status Packet is returned as '1' and Alarm is triggered as set
            in the Alarm LED and Alarm Shutdown.
            
            Parameters
            ----------
            motor_id : int
            The motor ID [0-253]
            lowest_limit_voltage : float
            Lowest operating voltage limit in volt [5V-25V]
            highest_limit_voltage : float
            Highest operating voltage limit in volt [5V-25V]
            
            """
        if not (5 <= lowest_limit_voltage <= 25) or not (5 <= highest_limit_voltage <= 25):
            raise ValueError('The lowest limit temperature must be in [5, 25].')
        if (highest_limit_voltage <= lowest_limit_voltage):
            raise ValueError('The highest limit voltage must be superior than the lowest limit voltage.')
        
        self._send_write_packet(motor_id,
                                'VOLTAGE_LIMITS',
                                (lowest_limit_voltage * 10, highest_limit_voltage * 10))
    
    def get_max_torque(self, motor_id):
        """ Returns the maximum output torque avaible in percent. """
        return self._send_read_packet(motor_id, 'MAX_TORQUE') * (100.0 / 1023)
    
    def set_max_torque(self, motor_id, max_torque):
        """ Sets the maximum output torque avaible in percent. """
        if not (0 <= max_torque <= 100):
            raise ValueError('The maximum torque must be in [0, 100].')
        
        self._send_write_packet(motor_id, 'MAX_TORQUE', int(max_torque * 10.23))
    
    
    def get_status_return_level(self, motor_id):
        return self._send_read_packet(motor_id, 'STATUS_RETURN_LEVEL')
    
    def set_status_return_level(self, motor_id, status_return_level):
        # TODO: what happened if we change to 0 or another value ?
        self._send_write_packet(motor_id, 'STATUS_RETURN_LEVEL', status_return_level)
    
    
    def get_alarm_led(self, motor_id):
        return self._send_read_packet(motor_id, 'ALARM_LED')
    
    def set_alarm_led(self, motor_id, alarm_led):
        self._send_write_packet(motor_id, 'ALARM_LED', int(alarm_led))
    
    
    def get_alarm_shutdown(self, motor_id):
        return self._send_read_packet(motor_id, 'ALARM_SHUTDOWN')
    
    def set_alarm_shutdown(self, motor_id, alarm_shutdown):
        self._send_write_packet(motor_id, 'ALARM_SHUTDOWN', int(alarm_shutdown))
    
    
    # MARK: - Dxl Motor RAM Access
    
    def is_torque_enabled(self, motor_id):
        """ Check if the torque is enabled for the specified motor. """
        return bool(self._send_read_packet(motor_id, 'TORQUE_ENABLE'))
    
    def enable_torque(self, motor_id):
        """ Enables the torque to the specified motor. """
        self._set_torque_enable(motor_id, True)
    
    def disable_torque(self, motor_id):
        """ Disables the torque to the specified motor. """
        self._set_torque_enable(motor_id, False)
    
    def _set_torque_enable(self, motor_id, torque_enable):
        self._send_write_packet(motor_id, 'TORQUE_ENABLE', int(torque_enable))
    
    
    def is_led_on(self, motor_id):
        """ Check if the led is on for the specified motor. """
        return bool(self._send_read_packet(motor_id, 'LED'))
    
    def turn_on_led(self, motor_id):
        """ Turn on the led of the specified motor. """
        self._set_led(motor_id, True)
    
    def turn_off_led(self, motor_id):
        """ Turn off the led of the specified motor. """
        self._set_led(motor_id, False)
    
    def _set_led(self, motor_id, on):
        self._send_write_packet(motor_id, 'LED', int(on))
    
    
    def get_pid_gains(self, motor_id):
        """
            Gets the PID gains for the specified motor.
            
            The P gain refers to the value of proportional band.
            The I gain refers to the value of integral action.
            The D gain refers to the value of derivative action.
            Gains values are in between [0-254].
            
            Returns
            -------
            [D gain, I gain, P gain]
            
            
            This method only exists for MX motors.
            
            See Also
            --------
            get_compliance_margins, get_compliance_slopes
            
            """
        motor_model = self._lazy_get_model(motor_id)
        if not motor_model.startswith('MX'):
            raise DynamixelUnsupportedFunctionForMotorError(self.get_pid_gains,
                                                            motor_id,
                                                            motor_model)
        
        return self._send_read_packet(motor_id, 'GAINS')
    
    def set_pid_gains(self, motor_id,
                      derivative_gain, integral_gain, proportional_gain):
        """
            Sets the PID gains for the specified motor.
            
            Parameters
            ----------
            motor_id : int
            The motor ID [0-253]
            derivative_gain : int
            The D gain refers to the value of derivative action [0-254].
            integral_gain : int
            The I gain refers to the value of integral action [0-254].
            proportional_gain : int
            The P gain refers to the value of proportional band [0-254].
            
            
            This method only exists for MX motors.
            
            See Also
            --------
            set_compliance_margins, set_compliance_slopes
            
            """
        motor_model = self._lazy_get_model(motor_id)
        if not motor_model.startswith('MX'):
            raise DynamixelUnsupportedFunctionForMotorError(self.get_pid_gains,
                                                            motor_id,
                                                            motor_model)
        
        self._send_write_packet(motor_id,
                                'GAINS',
                                (derivative_gain, integral_gain, proportional_gain))
    
    
    def get_compliance_margins(self, motor_id):
        """
            Gets the compliance margins of the specified motor.
            
            The compliance margin exists in each direction (CW and CCW) and
            means the error between goal position and present position.
            The greater the value, the more difference occurs.
            
            Returns
            -------
            (cw margin, ccw margin)
            
            This method has been replaced for MX motors.
            
            See Also
            --------
            get_pid_gains
            
            """
        motor_model = self._lazy_get_model(motor_id)
        if not (motor_model.startswith('AX') or motor_model.startswith('RX')):
            raise DynamixelUnsupportedFunctionForMotorError(self.get_compliance_margins,
                                                            motor_id,
                                                            motor_model)
        
        return self._send_read_packet(motor_id, 'COMPLIANCE_MARGINS')
    
    def set_compliance_margins(self, motor_id,
                               clockwise_margin, counterclockwise_margin):
        """
            Sets new compliance margins for the specified motors.
            
            The compliance margin exists in each direction (CW and CCW) and
            means the error between goal position and present position.
            The greater the value, the more difference occurs.
            
            Parameters
            ----------
            clockwise_margin : int [0, 255]
            counterclockwise_margin : int [0, 255]
            
            This method has been replaced for MX motors.
            
            See Also
            --------
            set_pid_gains
            
            """
        motor_model = self._lazy_get_model(motor_id)
        if not (motor_model.startswith('AX') or motor_model.startswith('RX')):
            raise DynamixelUnsupportedFunctionForMotorError(self.get_compliance_margins,
                                                            motor_id,
                                                            motor_model)
        self._send_write_packet(motor_id, 'COMPLIANCE_MARGINS',
                                (clockwise_margin, counterclockwise_margin))
    
    def get_compliance_slopes(self, motor_id):
        """
            Gets the compliance slopes of the specified motor.
            
            The compliance slope exists in each direction (CW and CCW) and
            sets the level of torque near the goal position.
            The higher the value, the more flexibility is obtained.
            
            Returns
            -------
            (cw slope, ccw slope)
            
            This method has been replaced for MX motors.
            
            See Also
            --------
            get_pid_gains
            
            """
        motor_model = self._lazy_get_model(motor_id)
        if not (motor_model.startswith('AX') or motor_model.startswith('RX')):
            raise DynamixelUnsupportedFunctionForMotorError(self.get_compliance_margins,
                                                            motor_id,
                                                            motor_model)
        
        return self._send_read_packet(motor_id, 'COMPLIANCE_SLOPES')
    
    def set_compliance_slopes(self, motor_id,
                              clockwise_slope, counterclockwise_slope):
        """
            Sets new compliance slopes for the specified motors.
            
            The compliance slope exists in each direction (CW and CCW) and
            sets the level of torque near the goal position.
            The higher the value, the more flexibility is obtained.
            
            Parameters
            ----------
            clockwise_slope : int [0, 255]
            counterclockwise_slope : int [0, 255]
            
            This method has been replaced for MX motors.
            
            See Also
            --------
            set_pid_gains
            
            """
        motor_model = self._lazy_get_model(motor_id)
        if not (motor_model.startswith('AX') or motor_model.startswith('RX')):
            raise DynamixelUnsupportedFunctionForMotorError(self.get_compliance_margins,
                                                            motor_id,
                                                            motor_model)
        
        self._send_write_packet(motor_id, 'COMPLIANCE_SLOPES',
                                (clockwise_slope, counterclockwise_slope))
    
    
    
    def get_position(self, motor_id):
        """ Returns the position in degrees of the specified motor. """
        return position_to_degree(self._send_read_packet(motor_id, 'PRESENT_POSITION'),
                                  self._lazy_get_model(motor_id))
    
    def set_position(self, motor_id, position):
        """ Sets the position in degrees of the specified motor. """
        self._send_write_packet(motor_id, 'GOAL_POSITION',
                                degree_to_position(position,
                                                   self._lazy_get_model(motor_id)))
    
    
    def get_speed(self, motor_id):
        """ Returns the speed in rpm (positive values correspond to clockwise) of the specified motor. """
        return speed_to_rpm(self._send_read_packet(motor_id, 'PRESENT_SPEED'))
    
    def set_speed(self, motor_id, speed):
        """ Sets the speed in rpm (positive values correspond to clockwise) of the specified motor. """
        self._send_write_packet(motor_id, 'MOVING_SPEED',
                                rpm_to_speed(speed))
    
    
    def get_torque_limit(self, motor_id):
        return self._send_read_packet(motor_id, 'TORQUE_LIMIT')
    
    def set_torque_limit(self, motor_id, torque_limit):
        self._send_write_packet(motor_id, 'TORQUE_LIMIT', torque_limit)
    
    
    def get_load(self, motor_id):
        """ Returns the internal load in percent of the specified motor. """
        return load_to_percent(self._send_read_packet(motor_id, 'PRESENT_LOAD'))
    
    
    def get_position_speed_load(self, motor_id):
        """ Returns the position, speed and internal load of the specified motor """
        pos, speed, load = self._send_read_packet(motor_id, 'PRESENT_POS_SPEED_LOAD')
        
        return (position_to_degree(pos, self._lazy_get_model(motor_id)),
                speed_to_rpm(speed),
                load_to_percent(load))
    
    
    def get_voltage(self, motor_id):
        """ Returns the current voltage supplied (V). """
        return self._send_read_packet(motor_id, 'PRESENT_VOLTAGE') * 0.1
    
    
    def get_temperature(self, motor_id):
        """ Returns the internal temperature of the specified motor (in Celsius). """
        return self._send_read_packet(motor_id, 'PRESENT_TEMPERATURE')
    
    
    # def is_registred(self, motor_id): # TODO: ca fait quoi ?
    #     return bool(self._send_read_packet(motor_id, 'REGISTERED'))
    
    
    def is_moving(self, motor_id):
        """ Checks if the motor is moving (whether goal position has been reached). """
        return bool(self._send_read_packet(motor_id, 'MOVING'))
    
    
    def is_eeprom_locked(self, motor_id):
        """ Checks if the EEPROM area can be modified. """
        return bool(self._send_read_packet(motor_id, 'LOCK'))
    
    def lock_eeprom(self, motor_id):
        """ Prevents the modification of the EEPROM area. """
        self._set_eeprom_lock(motor_id, True)
    
    # def unlock_eeprom(self, motor_id):
    #     raise DeprecationWarning('to unlock the eeprom, you should cycle power')
    
    #     self._set_eeprom_lock(motor_id, False)
    
    def _set_eeprom_lock(self, motor_id, lock_eeprom):
        self._send_write_packet(motor_id, 'LOCK', int(lock_eeprom))
    
    
    # def get_punch(self, motor_id):
    #     return self._send_read_packet(motor_id, 'PUNCH')
    
    # def set_punch(self, motor_id, punch):
    #     self._send_write_packet(motor_id, 'PUNCH', punch)
    
    
    # def get_sensed_current(self, motor_id):
    #     motor_model = self._lazy_get_model(motor_id)
    #     if not motor_model.startswith('EX'):
    #         raise DynamixelUnsupportedFunctionForMotorError(self.get_sensed_current,
    #                                                         motor_id,
    #                                                         motor_model)
    #     return self._send_read_packet(motor_id, 'SENSED_CURRENT')
    
    # def get_current(self, motor_id):
    #     motor_model = self._lazy_get_model(motor_id)
    #     if not motor_model in ('MX-64', 'MX-106'):
    #         raise DynamixelUnsupportedFunctionForMotorError(self.get_current,
    #                                                         motor_id,
    #                                                         motor_model)
    #     return self._send_read_packet(motor_id, 'CURRENT')
    
    # def set_current(self, motor_id, current):
    #     motor_model = self._lazy_get_model(motor_id)
    #     if not motor_model in ('MX-64', 'MX-106'):
    #         raise DynamixelUnsupportedFunctionForMotorError(self.get_current,
    #                                                         motor_id,
    #                                                         motor_model)
    #     self._send_write_packet(motor_id, 'CURRENT', current)
    
    
    # MARK: - Low level communication
    
    def _send_packet(self, packet, wait_for_answer=True):
        with self._lock:
            nbytes = self._serial.write(array.array('B', packet).tostring())
            if nbytes != len(packet):
                raise DynamixelCommunicationError('Packet not correctly sent',
                                                  packet[2],
                                                  packet,
                                                  None)
            
            if not wait_for_answer:
                return
            
            header = list(self._serial.read(4))
            if not header:
                raise DynamixelTimeoutError(packet[2], packet)
            
            if header[:2] != ['\xff', '\xff'] or len(header) != 4:
                raise DynamixelCommunicationError('Packet received with an inconsistent header',
                                                  packet[2],
                                                  packet,
                                                  header)
            
            motor_id, length = map(ord, header[2:])
            
            status_packet = map(ord, self._serial.read(length))
            if len(status_packet) != length or len(status_packet) < 2:
                raise DynamixelCommunicationError('Packet received with an inconsistent status packet',
                                                  packet[2],
                                                  packet,
                                                  header + status_packet)
            
            error_code = status_packet[0]
            parameters = status_packet[1:-1]
            checksum = status_packet[-1]
            
            if self._compute_checksum(motor_id, length, error_code, parameters) != checksum:
                raise DynamixelCommunicationError('Packet received with wrong checksum',
                                                  packet[2],
                                                  packet,
                                                  header + status_packet)
            
            if error_code != 0:
                raise DynamixelMotorError(motor_id, error_code)
            
            return parameters
    
    
    def _send_read_packet(self, motor_id, control_name):
        address, number_of_data, data_length = DXL_CONTROLS[control_name]
        
        packet = self._build_packet(motor_id,
                                    'READ_DATA',
                                    (address, number_of_data * data_length))
        
        answer = self._send_packet(packet)
        return self._decode_data(answer, data_length)
    
    
    def _send_sync_read_packet(self, motor_ids, control_name):
        address, number_of_data, data_length = DXL_CONTROLS[control_name]
        
        packet = self._build_packet(DXL_BROADCAST,
                                    'SYNC_READ',
                                    [address, number_of_data * data_length] + list(motor_ids))
        
        answer = self._send_packet(packet)
        
        return map(lambda data: self._decode_data(data, data_length),
                   reshape_list(answer, number_of_data * data_length))
    
    
    def _send_write_packet(self, motor_id, control_name, data):
        address, number_of_data, data_length = DXL_CONTROLS[control_name]
        
        data = self._code_data(data, data_length)
        
        if len(data) != number_of_data * data_length:
            raise ValueError('invalid data (%s) for the control (%s)' % (data, control_name))
        
        packet = self._build_packet(motor_id,
                                    'WRITE_DATA',
                                    [address] + data)
        
        self._send_packet(packet)
    
    def _send_sync_write_packet(self, control_name, data_tuples):
        address, number_of_data, data_length = DXL_CONTROLS[control_name]
        
        data = flatten_list(map(lambda chunk: [chunk[0]] + self._code_data(chunk[1:], data_length),
                                data_tuples))
        
        packet = self._build_packet(DXL_BROADCAST,
                                    'SYNC_WRITE',
                                    [address, number_of_data * data_length] + data)
        
        self._send_packet(packet, wait_for_answer=False)
    
    
    def _build_packet(self, motor_id, instruction_name, parameters=()):
        instruction = DXL_INSTRUCTIONS[instruction_name]
        
        length = len(parameters) + 2
        checksum = self._compute_checksum(motor_id, length, instruction, parameters)
        
        packet = [0xFF, 0xFF, motor_id, length, instruction] + list(parameters) + [checksum]
        
        return packet
    
    
    def _compute_checksum(self, motor_id, length, instruction, parameters):
        # Check Sum = ~ ( ID + Length + Instruction + Parameter1 + ... + Parameter N)
        return 255 - ((motor_id + length + instruction + sum(parameters)) % 256)
    
    
    # MARK : - Data coding/uncoding
    
    def _code_data(self, data, data_length):
        if data_length not in (1, 2):
            raise ValueError('Unsupported data length (%d)' % (data_length))
        
        if not hasattr(data, '__len__'):
            data = [data]
        
        if data_length == 2:
            data = flatten_list(map(integer_to_two_bytes, data))
        
        return list(data)
    
    def _decode_data(self, data, data_length):
        if data_length not in (1, 2):
            raise ValueError('Unsupported data length (%d)' % (data_length))
        
        if data_length == 2:
            data = map(two_bytes_to_integer, reshape_list(data, 2))
        return data if len(data) > 1 else data[0]


# MARK: - Dxl Error

class DynamixelIOError(Exception):
    def __init__(self, motor_id):
        self.motor_id = motor_id

class DynamixelCommunicationError(DynamixelIOError):
    def __init__(self, message, motor_id, sent_packet, received_packet):
        DynamixelIOError.__init__(self, motor_id)
        
        self.message = message
        self.sent_packet = sent_packet
        self.received_packet = received_packet
    
    def __str__(self):
        return '%s (Motor id:%d, sent packet: %s received packet: %s' % (self.message, self.motor_id, self.sent_packet, self.received_packet)

class DynamixelTimeoutError(DynamixelIOError):
    def __init__(self, motor_id, sent_packet):
        DynamixelIOError.__init__(self, motor_id)
        
        self.sent_packet = sent_packet
    
    def __str__(self):
        return 'Motor %d did not respond when sent packet %s' % (self.motor_id, self.sent_packet)


class DynamixelMotorError(Exception):
    def __init__(self, motor_id, error_code):
        self.motor_id = motor_id
        self.error_code = error_code
    
    def __str__(self):
        return 'Motor %d returned error code %d' % (self.motor_id, self.error_code)

class DynamixelUnsupportedMotorError(Exception):
    def __init__(self, motor_id, model_number):
        self.motor_id = motor_id
        self.model_number = model_number
    
    def __str__(self):
        return 'Unsupported Motor with id: %d and model number: %d' % (self.motor_id, self.model_number)

class DynamixelUnsupportedFunctionForMotorError(Exception):
    def __init__(self, func, motor_id, motor_model):
        self.func = func
        self.motor_id = motor_id
        self.motor_model = motor_model
    
    def __str__(self):
        return 'Unsupported function (%s) for motor (%d: %s)' % (self.func.__name__, self.motor_id, self.motor_model)

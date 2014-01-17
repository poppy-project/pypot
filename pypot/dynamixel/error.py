# -*- coding: utf-8 -*-

import logging


class DxlErrorHandler(object):
    """ This class is used to represent all the error that you can/should handle.

        The errors can be of two types:

        * communication error (timeout, communication)
        * motor error (voltage, limit, overload...)

        This class was designed as an abstract class and so you should write your own handler by subclassing this class and defining the apropriate behavior for your program.

        .. warning:: The motor error should be overload carrefuly as they can indicate important mechanical issue.

        """
    # MARK: - Communication errors

    def handle_timeout(self, timeout_error):
        raise NotImplementedError

    def handle_communication_error(self, communication_error):
        raise NotImplementedError


    # MARK: - Motor errors

    def handle_input_voltage_error(self, instruction_packet):
        raise NotImplementedError

    def handle_angle_limit_error(self, instruction_packet):
        raise NotImplementedError

    def handle_overheating_error(self, instruction_packet):
        raise NotImplementedError

    def handle_range_error(self, instruction_packet):
        raise NotImplementedError

    def handle_checksum_error(self, instruction_packet):
        raise NotImplementedError

    def handle_overload_error(self, instruction_packet):
        raise NotImplementedError

    def handle_instruction_error(self, instruction_packet):
        raise NotImplementedError

    def handle_none_error(self, instruction_packet):
        raise NotImplementedError


class BaseErrorHandler(DxlErrorHandler):
    """ This class is a basic handler that just skip the communication errors. """
    def handle_timeout(self, timeout_error):
        logging.warning('timeout occured in motors {} after sending {}'.format(timeout_error.ids,
                                                                               timeout_error.instruction_packet))

    def handle_communication_error(self, communication_error):
        logging.warning('communication error after sending {}'.format(communication_error.instruction_packet))

    def handle_overheating_error(self, instruction_packet):
        logging.error('overheating after sending {}'.format(instruction_packet))

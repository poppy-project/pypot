# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


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
        msg = 'Timeout after sending {} to motors {}'.format(timeout_error.instruction_packet,
                                                             timeout_error.ids)
        logger.warning(msg,
                       extra={'port': timeout_error.dxl_io.port,
                              'baudrate': timeout_error.dxl_io.baudrate,
                              'timeout': timeout_error.dxl_io.timeout})

    def handle_communication_error(self, com_error):
        msg = 'Communication error after sending {}'.format(com_error.instruction_packet)

        logger.warning(msg,
                       extra={'port': com_error.dxl_io.port,
                              'baudrate': com_error.dxl_io.baudrate,
                              'timeout': com_error.dxl_io.timeout})

    def handle_none_error(self, instruction_packet):
        logger.info('None Error!')

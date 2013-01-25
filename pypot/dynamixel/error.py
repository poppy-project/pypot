# -*- coding: utf-8 -*-

import logging

class DynamixelErrorHandler(object):
    """ This class is used to represent all the error that you can/should handle. 
        
        You should write your own handler by subclassing this class.
        
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



class BaseErrorHandler(DynamixelErrorHandler):
    """ This class is a basic handler that just skip most errors. """
    def handle_timeout(self, timeout_error):
        logging.warning('timeout occured in motors {} after sending {}'.format(timeout_error.ids,
                                                                               timeout_error.instruction_packet))

    def handle_communication_error(self, communication_error):
        logging.warning('communication error after sending {}'.format(communication_error.instruction_packet))

    def handle_overheating_error(self, instruction_packet):
        logging.error('overheating after sending {}'.format(instruction_packet))
        import sys
        sys.exit(1)

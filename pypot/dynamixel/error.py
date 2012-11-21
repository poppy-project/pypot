# -*- coding: utf-8 -*-

import logging

class DynamixelErrorHandler(object):
    """ This class is used to represent all the error that a handler should handle. 
        
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
    """ This class is a basic handler that can directly be used. """
    def handle_timeout(self, timeout_error):
        logging.warning('timeout occured after sending {}'.format(timeout_error.instruction_packet))


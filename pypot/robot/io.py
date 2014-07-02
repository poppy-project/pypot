from abc import ABCMeta, abstractmethod


class AbstractIO(object):
    __metaclass__ = ABCMeta
    """ AbstractIO class which handles communication with "hardware" motors. """

    @abstractmethod
    def close(self):
        """ Clean and close the IO connection. """
        pass

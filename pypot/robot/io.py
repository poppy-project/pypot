from abc import ABCMeta, abstractmethod


class AbstractIO(object):
    """ AbstractIO class which handles communication with "hardware" motors. """

    __metaclass__ = ABCMeta

    @abstractmethod
    def close(self):
        """ Clean and close the IO connection. """
        pass

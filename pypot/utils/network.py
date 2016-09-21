import errno
import socket
import logging

from contextlib import closing


logger = logging.getLogger(__name__)


def find_local_ip(host=None):
    # see here: http://stackoverflow.com/questions/166506/
    try:
        if host is None:
            host = socket.gethostname()

        if 'local' not in host:
            host += '.local'

        try:
            ips = [ip for ip in socket.gethostbyname_ex(host)[2]
                   if not ip.startswith('127.')]
            if len(ips):
                return ips[0]
        except socket.gaierror:
            logger.debug('socket gaierror with hostname {}'.format(host))
            pass

        # If the above method fails (depending on the system)
        # Tries to ping google DNS instead (need a internet connexion)
        try:
            with closing(socket.socket()) as s:
                s.settimeout(1)
                s.connect(('8.8.8.8', 53))
                return s.getsockname()[0]
        except socket.timeout:
            logger.debug('socket timeout')
            pass

    except IOError as e:
        # network unreachable
        if e.errno == errno.ENETUNREACH:
            logger.debug('network unreachable')
            pass
        else:
            raise
    return '127.0.0.1'

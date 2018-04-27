import threading

import keyboard
import zmq
import json
import logging

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from .server import AbstractServer

logger = logging.getLogger(__name__)


class ZMQRobotServer(AbstractServer):
    def __init__(self, robot, host, port, with_keylogger=False):
        """ A ZMQServer allowing remote access of a robot instance.

        The server used the REQ/REP zmq pattern. You should always first send a request and then read the answer.

        """
        AbstractServer.__init__(self, robot, host, port)

        c = zmq.Context()
        self.socket = c.socket(zmq.PAIR)
        self.socket.bind('tcp://{}:{}'.format(self.host, self.port))

        logger.info('Starting ZMQServer on tcp://%s:%s', self.host, self.port)

        self.with_keylogger = with_keylogger
        if with_keylogger:
            self.queue_ = Queue()
            self.killswitch = Queue()

            keylogger = Keylogger(self.queue_, self.killswitch)
            keylogger.start()

    def run(self):
        """ Run an infinite REQ/RES loop. """
        while True:
            req = self.socket.recv_json()

            try:
                answer = self.handle_request(req)
                self.socket.send(json.dumps(answer))

            except (AttributeError, TypeError) as e:
                self.socket.send_json({'error': str(e)})


    def decode(self, value):
        # type guessing

        value = value.encode('utf-8')
        try:
            v = float(value)
        except ValueError:
            try:
                v = int(value)
            except ValueError:
                v = str(value)
        return v

    def _get_keys(self):
        keys = []
        while not self.queue_.empty():
            keys.append(self.queue_.get())

        return keys

    def handle_request(self, request):
        meth_name, kwargs = request['robot'].popitem()

        if meth_name == "get_keys":
            if not self.with_keylogger:
                print ("ERROR: service wasn't started with keylogger attached. "
                       "You need to add '--with-keylogger' to the poppy-services call and then run the server with sudo")
            return self._get_keys()

        else:
            meth = getattr(self.restful_robot, meth_name)

            for key in ('value', 'args'):
                if key in kwargs:
                    kwargs[key] = self.decode(kwargs[key])

            ret = meth(**kwargs)
            ret = {} if ret is None else ret

            return ret

    def __del__(self):
        self.killswitch.put("quit")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

class Keylogger(threading.Thread):
    def __init__(self, q, ks):
        threading.Thread.__init__(self)
        self._queue = q
        self._killswitch = ks
        keyboard.add_hotkey('w', self.add, args="w")
        keyboard.add_hotkey('a', self.add, args="a")
        keyboard.add_hotkey('s', self.add, args="s")
        keyboard.add_hotkey('d', self.add, args="d")
        keyboard.add_hotkey(' ', self.add, args=" ")
        # keyboard.add_hotkey(' ', self.add, args=['space was pressed'])

    def add(self, key):
        self._queue.put(key)

    def run(self):
        try:
            while True:
                # queue.get() blocks the current thread until
                # an item is retrieved.
                msg = self._killswitch.get()
                # Checks if the current message is
                # the "Poison Pill"
                if isinstance(msg, str) and msg == 'quit':
                    # if so, exists the loop
                    break
                # "Processes" (or in our case, prints) the queue item
                print("I'm a thread, and I received %s!!" % msg)
        except KeyboardInterrupt:
            pass

        # Always be friendly!
        print('Bye byes!')

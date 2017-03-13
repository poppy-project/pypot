from __future__ import division

import time
import json

from threading import Timer

from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler
from tornado.web import Application

from .server import AbstractServer


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.function(*self.args, **self.kwargs)
        self.start()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class WsSocketHandler(WebSocketHandler):
    time_step = 1 / 30

    def check_origin(self, origin):
        return True

    def open(self):
        if not self.quiet:
            print('WebSocket connection open.')

        self.rt = RepeatedTimer(self.time_step, self.publish_robot_state)

    def on_close(self):
        if not self.quiet:
            print('WebSocket connection closed: {0}'.format(self.close_reason))
        self.rt.stop()

    def on_message(self, message):
        if not self.quiet:
            print('{}: Received {}'.format(time.time(), message))

        self.handle_command(json.loads(message))

    def publish_robot_state(self):
        state = {
            m.name: {
                'present_position': m.present_position,
                'present_speed': m.present_speed,
                'present_load': m.present_load,
                'led': m.led,
                'present_temperature': m.present_temperature,
            }
            for m in self.robot.motors
        }
        self.write_message(json.dumps(state))

    def handle_command(self, command):
        for motor, values in command.items():
            m = getattr(self.robot, motor)

            for register, value in values.items():
                setattr(m, register, value)


class WsRobotServer(AbstractServer):
    def __init__(self, robot, host='0.0.0.0', port='9009', quiet=True):
        AbstractServer.__init__(self, robot, host, port)
        WsSocketHandler.robot = robot
        WsSocketHandler.quiet = quiet

    def run(self):
        loop = IOLoop()
        app = Application([
            (r'/', WsSocketHandler)
        ])
        app.listen(self.port)
        loop.start()

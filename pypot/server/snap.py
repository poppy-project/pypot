import os
import bottle
import socket

from .server import AbstractServer


def make_snap_compatible_response(f):
    def wrapped_f(*args, **kwargs):
        msg = f(*args, **kwargs)

        r = bottle.response
        r.status = '200 OK'
        r.set_header('Content-Type', 'text/html')
        r.set_header('charset', 'ISO-8859-1')
        r.set_header('Content-Length', len(msg))
        r.set_header('Access-Control-Allow-Origin', '*')

        return msg

    return wrapped_f


class SnapRobotServer(AbstractServer):
    def __init__(self, robot, host, port):
        AbstractServer.__init__(self, robot, host, port)

        self.app = bottle.Bottle()

        rr = self.restfull_robot

        @self.app.get('/motors/<alias>')
        @make_snap_compatible_response
        def get_motors(alias):
            return '/'.join(rr.get_motors_list(alias))

        @self.app.get('/motor/<motor>/get/<register>')
        @make_snap_compatible_response
        def get_motor_register(motor, register):
            return str(rr.get_motor_register_value(motor, register))

        @self.app.get('/motors/get/positions')
        @make_snap_compatible_response
        def get_motors_positions():
            get_pos = lambda m: rr.get_motor_register_value(m, 'present_position')
            msg = '/'.join('{}'.format(get_pos(m)) for m in rr.get_motors_list())
            msg = ';'.join('{}'.format(get_pos(m)) for m in rr.get_motors_list())
            return msg

        @self.app.get('/motors/set/positions/<positions>')
        @make_snap_compatible_response
        def set_motors_positions(positions):
            positions = map(lambda s: float(s), positions[:-1].split(';'))

            for m, p in zip(rr.get_motors_list(), positions):
                rr.set_motor_register_value(m, 'goal_position', p)

            return 'Done!'

        @self.app.get('/motor/<motor>/set/<register>/<value>')
        @make_snap_compatible_response
        def set_reg(motor, register, value):
            rr.set_motor_register_value(motor, register, float(value))
            return 'Done!'

        @self.app.get('/motor/<motor>/goto/<position>/<duration>')
        @make_snap_compatible_response
        def set_goto(motor, position, duration):
            rr.set_goto_position_for_motor(motor, float(position), float(duration))
            return 'Done!'

        @self.app.get('/snap-blocks.xml')
        @make_snap_compatible_response
        def get_pypot_snap_blocks():
            with open(os.path.join(os.path.dirname(__file__),
                      'pypot-snap-blocks.xml')) as f:
                return f.read()

        @self.app.get('/ip')
        @make_snap_compatible_response
        def get_ip():
            return socket.gethostbyname(socket.gethostname())

        @self.app.get('/reset-simulation')
        @make_snap_compatible_response
        def reset_simulation():
            if hasattr(robot, 'reset_simulation'):
                robot.reset_simulation()
            return 'Done!'

    def run(self):
        bottle.run(self.app,
                   host=self.host, port=self.port,
                   quiet=True)

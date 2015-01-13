import bottle

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


        @self.app.get('/motor/<motor>/set/<register>/<value>')
        @make_snap_compatible_response
        def set_pos(motor, register, value):
            rr.set_motor_register_value(motor, register, float(value))
            return 'done!'

        print 'Snap Server should now be ready!'

    def run(self):
        try:
            bottle.run(self.app,
                       host=self.host, port=self.port,
                       quiet=True,
                       server='tornado')
        except KeyboardInterrupt:
            pass

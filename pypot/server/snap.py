import bottle

from .server import AbstractServer



class SnapRobotServer(AbstractServer):
    def __init__(self, robot, host, port):
        AbstractServer.__init__(self, robot, host, port)

        self.app = bottle.Bottle()

        rr = self.restfull_robot

        @self.app.get('/motors')
        def get_motors():
            print '/'.join(rr.get_motors_list())
            return '/'.join(rr.get_motors_list())

        @self.app.get('/motor/<motor>/get/<register>')
        def get_motor_register(motor, register):
            s = str(rr.get_motor_register_value(motor, register))

            r = bottle.response
            r.status = '200 OK'
            r.set_header('Content-Type', 'text/html')
            r.set_header('charset', 'ISO-8859-1')
            r.set_header('Content-Length', len(s))
            r.set_header('Access-Control-Allow-Origin', '*')


            return s

        @self.app.get('/motor/<motor>/set/<register>/<value>')
        def set_pos(motor, register, value):
            rr.set_motor_register_value(motor, register, float(value))

            s = str('done!')

            r = bottle.response
            r.status = '200 OK'
            r.set_header('Content-Type', 'text/html')
            r.set_header('charset', 'ISO-8859-1')
            r.set_header('Content-Length', len(s))
            r.set_header('Access-Control-Allow-Origin', '*')

            # t.append(time.time())

            return s
        print 'Snap Server should now be ready!'

    def run(self):
        try:
            bottle.run(self.app,
                       host=self.host, port=self.port,
                       quiet=True,
                       server='tornado')
        except KeyboardInterrupt:
            pass

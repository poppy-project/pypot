import os
import bottle
import socket

from .server import AbstractServer

from pypot.primitive.move import MovePlayer, MoveRecorder, Move
from pypot.primitive.utils import Cosinus, Sinus, LoopPrimitive, numpy


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
            get_pos = lambda m: rr.get_motor_register_value(
                m, 'present_position')
            msg = '/'.join('{}'.format(get_pos(m))
                           for m in rr.get_motors_list())
            msg = ';'.join('{}'.format(get_pos(m))
                           for m in rr.get_motors_list())
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
            rr.set_goto_position_for_motor(
                motor, float(position), float(duration))
            return 'Done!'

        @self.app.get('/snap-blocks.xml')
        @make_snap_compatible_response
        def get_pypot_snap_blocks():
            with open(os.path.join(os.path.dirname(__file__), 'pypot-snap-blocks.xml')) as f:
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

        @self.app.get('/primitives')
        @make_snap_compatible_response
        def get_primitives():
            return '/'.join(rr.get_primitives_list())

        @self.app.get('/primitives/running')
        @make_snap_compatible_response
        def get_running_primitives():
            return '/'.join(rr.get_running_primitives_list())

        @self.app.get('/primitive/<primitive>/start')
        @make_snap_compatible_response
        def start_primitive(primitive):
            rr.start_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/stop')
        @make_snap_compatible_response
        def stop_primitive(primitive):
            rr.stop_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/pause')
        @make_snap_compatible_response
        def pause_primitive(primitive):
            rr.pause_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/resume')
        @make_snap_compatible_response
        def resume_primitive(primitive):
            rr.resume_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/properties')
        @make_snap_compatible_response
        def get_primitive_properties_list(primitive):
            return rr.get_primitive_properties_list(primitive)

        @self.app.get('/primitive/<primitive>/get/<property>')
        @make_snap_compatible_response
        def get_primitive_property(primitive, property):
            return rr.get_primitive_property(primitive, property)

        @self.app.get('/primitive/<primitive>/set/<property>/<value>')
        @make_snap_compatible_response
        def set_primitive_property(primitive, property, value):
            return rr.set_primitive_property(primitive, property, value)

        @self.app.get('/primitive/<primitive>/methodes')
        @make_snap_compatible_response
        def get_primitive_methodes_list(primitive):
            return rr.get_primitive_properties_list(primitive)

        @self.app.get('/primitive/<primitive>/call/<methode_name>/<arg>')
        @make_snap_compatible_response
        def call_primitive_methode(primitive):
            return rr.get_primitive_properties_list(primitive)

        # Hacks (no restfull) to record movements
        # TODO allow to choose motors motors
        @self.app.get('/primitive/MoveRecorder/<move_name>/start')
        @make_snap_compatible_response
        def start_move_recorder(move_name):
            rr.start_move_recorder(move_name, rr.get_motors_list('motors'))
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/stop')
        @make_snap_compatible_response
        def stop_move_recorder(move_name):
            rr.stop_move_recorder(move_name)
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/remove')
        @make_snap_compatible_response
        def remove_move_record(move_name):
            rr.remove_move_record(move_name)
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder')
        @make_snap_compatible_response
        def get_available_records():
            return '/'.join(rr.get_available_record_list())

        @self.app.get('/primitive/MovePlayer')
        @make_snap_compatible_response
        def get_available_records():
            return '/'.join(rr.get_available_record_list())

        @self.app.get('/primitive/MovePlayer/<move_name>/start')
        @make_snap_compatible_response
        def start_move_player(move_name):
            primitive_name = rr.start_move_player(move_name)
            return 'Done!'

        @self.app.get('/primitive/MovePlayer/<move_name>/stop')
        @make_snap_compatible_response
        def stop_move_player(move_name):
            rr.stop_primitive(move_name + '_player')
            return 'Done!'

    def run(self):
        bottle.run(self.app, host=self.host, port=self.port, quiet=True)

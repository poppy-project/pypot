
import os
import bottle
import socket
from string import Template

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


def make_xml_from_templates(host, port, template_extension='.snapTemplate'):
    """ Allow to change dynamically port and host variable in xml Snap! project file"""
    template_files = [f for f in os.listdir('.') if f.endswith(template_extension)]
    d = {'host': host, 'port': port}
    for template in template_files:
        with open(template, 'r') as tf:
            xml = Template(tf.read()).substitute(d)
            with open(template.split(template_extension)[0], 'w') as xf:
                xf.write(xml)


class SnapRobotServer(AbstractServer):

    def __init__(self, robot, host, port):
        AbstractServer.__init__(self, robot, host, port)

        self.app = bottle.Bottle()

        rr = self.restfull_robot

        make_xml_from_templates(host, port)

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

        @self.app.get('/motors/alias')
        @make_snap_compatible_response
        def get_robot_alias():
            return ';'.join('{}'.format(alias) for alias in rr.get_motors_alias())

        @self.app.get('/motors/set/goto/<motors_position_duration>')
        @make_snap_compatible_response
        def set_motors_positions(motors_position_duration):
            """ Allow lot of motors position settings with a single http request
                Be carefull: with lot of motors, it could overlap the GET max
                    lentgh of your web browser
                """
            for m_settings in motors_position_duration.split(';'):
                settings = m_settings.split(':')
                rr.set_goto_position_for_motor(settings[0], float(settings[1]), float(settings[2]))
            return 'Done!'

        @self.app.get('/motors/set/registers/<motors_register_value>')
        @make_snap_compatible_response
        def set_motors_registers(motors_register_value):
            """ Allow lot of motors register settings with a single http request
                Be carefull: with lot of motors, it could overlap the GET max
                    lentgh of your web browser
                """
            for m_settings in motors_register_value.split(';'):
                settings = m_settings.split(':')
                rr.set_motor_register_value(settings[0], settings[1], float(settings[2]))
            return 'Done!'

        # TODO : delete ?
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

        # TODO (Theo) : dynamic modification to change host and port automatically
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
        @self.app.get('/primitive/MoveRecorder/<move_name>/start')
        @make_snap_compatible_response
        def start_move_recorder(move_name):
            rr.start_move_recorder(move_name, rr.get_motors_list('motors'))
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/start/<motors>')
        @make_snap_compatible_response
        def start_move_recorder(move_name, motors):
            rr.start_move_recorder(move_name, motors.split(';'))
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
            return str(rr.start_move_player(move_name))

        @self.app.get('/primitive/MovePlayer/<move_name>/start/<move_speed>')
        @make_snap_compatible_response
        def start_move_player_with_speed(move_name, move_speed):
            return str(rr.start_move_player(move_name, float(move_speed)))

        @self.app.get('/primitive/MovePlayer/<move_name>/stop')
        @make_snap_compatible_response
        def stop_move_player(move_name):
            rr.stop_primitive('{}_player'.format(move_name))
            return 'Done!'

    def run(self):
        bottle.run(self.app, host=self.host, port=self.port, quiet=True)

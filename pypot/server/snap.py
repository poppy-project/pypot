
import os
import bottle
import socket
import re
import logging

from .server import AbstractServer
from.httpserver import EnableCors

logger = logging.getLogger(__name__)


def find_local_ip():
    # see here: http://stackoverflow.com/questions/166506/
    return [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close())
            for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


def set_snap_server_variables(host, port, snap_extension='.xml', path=None):
    """ Allow to change dynamically port and host variable in xml Snap! project file"""

    localdir = os.getcwd()
    if path is None:
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
    else:
        os.chdir(path)
    xml_files = [f for f in os.listdir('.') if f.endswith(snap_extension)]
    for filename in xml_files:
        with open(filename, 'r') as xf:
            xml = xf.read()
        with open(filename, 'w') as xf:
            xml = re.sub(r'''<variable name="host"><l>[\s\S]*?<\/l><\/variable>''',
                         '''<variable name="host"><l>{}</l></variable>'''.format(host), xml)
            xml = re.sub(r'''<variable name="port"><l>[\s\S]*?<\/l><\/variable>''',
                         '''<variable name="port"><l>{}</l></variable>'''.format(port), xml)
            xf.write(xml)
    os.chdir(localdir)


class SnapRobotServer(AbstractServer):

    def __init__(self, robot, host, port, quiet=True):
        AbstractServer.__init__(self, robot, host, port)
        self.quiet = quiet
        self.app = bottle.Bottle()
        self.app.install(EnableCors())

        rr = self.restfull_robot
        set_snap_server_variables(find_local_ip(), port)

        @self.app.get('/motors/<alias>')
        def get_motors(alias):
            return '/'.join(rr.get_motors_list(alias))

        @self.app.get('/motor/<motor>/get/<register>')
        def get_motor_register(motor, register):
            return str(rr.get_motor_register_value(motor, register))

        @self.app.get('/motors/get/positions')
        def get_motors_positions():
            get_pos = lambda m: rr.get_motor_register_value(
                m, 'present_position')
            msg = '/'.join('{}'.format(get_pos(m))
                           for m in rr.get_motors_list())
            msg = ';'.join('{}'.format(get_pos(m))
                           for m in rr.get_motors_list())
            return msg

        @self.app.get('/motors/alias')
        def get_robot_aliases():
            return '/'.join('{}'.format(alias) for alias in rr.get_motors_alias())

        @self.app.get('/motors/set/goto/<motors_position_duration>')
        def set_motors_goto(motors_position_duration):
            """ Allow lot of motors position settings with a single http request
                Be carefull: with lot of motors, it could overlap the GET max
                    lentgh of your web browser
                """
            for m_settings in motors_position_duration.split(';'):
                settings = m_settings.split(':')
                rr.set_goto_position_for_motor(settings[0], float(settings[1]), float(settings[2]))
            return 'Done!'

        @self.app.get('/motors/set/registers/<motors_register_value>')
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
        def set_motors_positions(positions):
            positions = map(lambda s: float(s), positions[:-1].split(';'))
            for m, p in zip(rr.get_motors_list(), positions):
                rr.set_motor_register_value(m, 'goal_position', p)
            return 'Done!'

        @self.app.get('/motor/<motor>/set/<register>/<value>')
        def set_reg(motor, register, value):
            rr.set_motor_register_value(motor, register, float(value))
            return 'Done!'

        @self.app.get('/motor/<motor>/goto/<position>/<duration>')
        def set_goto(motor, position, duration):
            rr.set_goto_position_for_motor(
                motor, float(position), float(duration))
            return 'Done!'

        @self.app.get('/snap-blocks.xml')
        def get_pypot_snap_blocks():
            with open(os.path.join(os.path.dirname(__file__), 'pypot-snap-blocks.xml')) as f:
                return f.read()

        @self.app.get('/ip')
        def get_ip():
            return socket.gethostbyname(socket.gethostname())

        @self.app.get('/reset-simulation')
        def reset_simulation():
            if hasattr(robot, 'reset_simulation'):
                robot.reset_simulation()
            return 'Done!'

        @self.app.get('/primitives')
        def get_primitives():
            return '/'.join(rr.get_primitives_list())

        @self.app.get('/primitives/running')
        def get_running_primitives():
            return '/'.join(rr.get_running_primitives_list())

        @self.app.get('/primitive/<primitive>/start')
        def start_primitive(primitive):
            rr.start_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/stop')
        def stop_primitive(primitive):
            rr.stop_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/pause')
        def pause_primitive(primitive):
            rr.pause_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/resume')
        def resume_primitive(primitive):
            rr.resume_primitive(primitive)
            return 'Done!'

        @self.app.get('/primitive/<primitive>/properties')
        def get_primitive_properties_list(primitive):
            return '/'.join(rr.get_primitive_properties_list(primitive))

        @self.app.get('/primitive/<primitive>/get/<property>')
        def get_primitive_property(primitive, property):
            return rr.get_primitive_property(primitive, property)

        @self.app.get('/primitive/<primitive>/set/<property>/<value>')
        def set_primitive_property(primitive, property, value):
            return rr.set_primitive_property(primitive, property, value)

        @self.app.get('/primitive/<primitive>/methodes')
        def get_primitive_methodes_list(primitive):
            return '/'.join(rr.get_primitive_methods_list(primitive))

        @self.app.get('/primitive/<primitive>/call/<method>/<args>')
        def call_primitive_methode(primitive, method, args):
            kwargs = dict(item.split(":") for item in args.split(";"))
            return rr._call_primitive_method(primitive, method, **kwargs)

        # Hacks (no restfull) to record movements
        @self.app.get('/primitive/MoveRecorder/<move_name>/start')
        def start_move_recorder(move_name):
            rr.start_move_recorder(move_name)
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/stop')
        def stop_move_recorder(move_name):
            rr.stop_move_recorder(move_name)
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/attach/<motors>')
        def start_move_recorder(move_name, motors):
            rr.attach_move_recorder(move_name, motors.split(';'))
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/get_motors')
        def get_move_recorder_motors(move_name):
            motors = rr.get_move_recorder_motors(move_name)
            return '/'.join(motors) if motors is not None else 'None'

        # Obsolete ?
        @self.app.get('/primitive/MoveRecorder/<move_name>/start/<motors>')
        def start_move_recorder_with_motors(move_name, motors):
            raise DeprecationWarning
            rr.start_move_recorder(move_name, motors.split(';'))
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/remove')
        def remove_move_record(move_name):
            rr.remove_move_record(move_name)
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder')
        def get_available_records():
            return '/'.join(rr.get_available_record_list())

        @self.app.get('/primitive/MovePlayer')
        def get_available_records():
            return '/'.join(rr.get_available_record_list())

        @self.app.get('/primitive/MovePlayer/<move_name>/start')
        def start_move_player(move_name):
            return str(rr.start_move_player(move_name))

        @self.app.get('/primitive/MovePlayer/<move_name>/start/<move_speed>')
        def start_move_player_with_speed(move_name, move_speed):
            return str(rr.start_move_player(move_name, float(move_speed)))

        @self.app.get('/primitive/MovePlayer/<move_name>/start/<move_speed>/backwards')
        def start_move_player_backwards_with_speed(move_name, move_speed):
            return str(rr.start_move_player(move_name, float(move_speed), backwards=True))

        @self.app.get('/primitive/MovePlayer/<move_name>/stop')
        def stop_move_player(move_name):
            rr.stop_primitive('_{}_player'.format(move_name))
            return 'Done!'

    def run(self):
        bottle.run(self.app, host=self.host, port=self.port, quiet=self.quiet)

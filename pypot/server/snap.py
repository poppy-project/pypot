import os
import re
import cgi
import numpy
import errno
import shutil
import bottle
import socket
import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from contextlib import closing
from ast import literal_eval as make_tuple

from .server import AbstractServer
from .httpserver import EnableCors
from ..utils.appdirs import user_data_dir


logger = logging.getLogger(__name__)


def get_snap_user_projects_directory():
    snap_user_projects_directory = user_data_dir('pypot', 'SnapRobotServer')
    if not os.path.exists(snap_user_projects_directory):
        os.makedirs(snap_user_projects_directory)
    return snap_user_projects_directory


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
        # error no 10065 = WSAESERVERUNREACH Windows Network unreachable
        if e.errno == errno.ENETUNREACH or e.errno == 10065:
            logger.debug('network unreachable')
            pass
        else:
            raise
    return '127.0.0.1'


def set_snap_server_variables(host, port, snap_extension='.xml', path=None):
    """ Change dynamically port and host variable in xml Snap! project file"""

    localdir = os.getcwd()
    if path is None:
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
    else:
        os.chdir(path)
    xml_files = [f for f in os.listdir('.') if f.endswith(snap_extension)]
    for filename in xml_files:
        with open(filename, 'r') as xf:
            xml = xf.read()
        # Change host variable
        xml = re.sub(r'''<variable name="host"><l>[\s\S]*?<\/l><\/variable>''',
                     '''<variable name="host"><l>{}</l></variable>'''.format(host), xml)
        # Change host argument of "set $robot host"
        xml = re.sub(r'''<custom-block s="set \$robot host to \%s"><l>[\s\S]*?<\/l>''',
                     '''<custom-block s="set $robot host to %s"><l>{}</l>'''.format(host), xml)
        # Change port variable
        xml = re.sub(r'''<variable name="port"><l>[\s\S]*?<\/l><\/variable>''',
                     '''<variable name="port"><l>{}</l></variable>'''.format(port), xml)

        with open(filename, 'w') as xf:
            xf.write(xml)
    os.chdir(localdir)


class SnapRobotServer(AbstractServer):

    def __init__(self, robot, host='0.0.0.0', port='6969', quiet=True):
        AbstractServer.__init__(self, robot, host, port)
        self.quiet = quiet
        self.app = bottle.Bottle()
        self.app.install(EnableCors())

        rr = self.restfull_robot

        # Copy Snap files from system directory to user directory. It avoids
        # right issue while PyPot is installed from pip in an admin directory
        snap_system_projects_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'snap_projects')
        xml_files = [os.path.join(snap_system_projects_directory, f)
                     for f in os.listdir(snap_system_projects_directory) if f.endswith('.xml')]
        for xml_file in xml_files:
            dst = os.path.join(get_snap_user_projects_directory(), os.path.basename(xml_file))
            logger.info('Copy snap project from {}, to {}'.format(xml_file, dst))
            shutil.copyfile(xml_file, dst)

        set_snap_server_variables(find_local_ip(), port, path=get_snap_user_projects_directory())

        @self.app.get('/')
        def get_sitemap():
            return '</br>'.join([cgi.escape(r.rule.format()) for r in self.app.routes])

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

        @self.app.get('/motors/<motors>/get/<register>')
        def get_motors_registers(motors, register):
            """ Allow getting of motors register with a single http request
                Be carefull: with lot of motors, it could overlap the GET max
                    lentgh of your web browser
                """
            motors = motors.split(';')
            return ';'.join(str(rr.get_register_value(m, register)) for m in motors)

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
                motor, register, value = m_settings.split(':')
                if register not in ('led'):
                    value = make_tuple(value)
                rr.set_motor_register_value(motor, register, value)
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
            if register not in ('led'):
                value = make_tuple(value)
            rr.set_motor_register_value(motor, register, value)
            return 'Done!'

        @self.app.get('/motor/<motor>/goto/<position>/<duration>')
        def set_goto(motor, position, duration):
            rr.set_goto_position_for_motor(
                motor, float(position), float(duration))
            return 'Done!'

        @self.app.get('/snap-blocks.xml')
        def get_pypot_snap_blocks():
            with open(os.path.join(get_snap_user_projects_directory(), 'pypot-snap-blocks.xml')) as f:
                return f.read()

        @self.app.get('/snap/<project>')
        def get_snap_projects(project):
            with open(os.path.join(get_snap_user_projects_directory(),
                                   '{}.xml'.format(project))) as f:
                return f.read()

        @self.app.get('/ip/')
        @self.app.get('/ip/<host>')
        def get_ip(host=None):
            return find_local_ip(host)

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
        @self.app.get('/primitive/<primitive>/call/<method>')
        def call_primitive_methode(primitive, method, args=None):
            if args is not None:
                kwargs = dict(item.split(":") for item in args.split(";"))
            else:
                kwargs = {}
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
        def attach_move_recorder(move_name, motors):
            rr.attach_move_recorder(move_name, motors.split(';'))
            return 'Done!'

        @self.app.get('/primitive/MoveRecorder/<move_name>/get_motors')
        def get_move_recorder_motors(move_name):
            motors = rr.get_move_recorder_motors(move_name)
            return '/'.join(motors) if motors is not None else 'None'

        @self.app.get('/primitive/MoveRecorder/<move_name>/start/<motors>')
        def start_move_recorder_with_motors(move_name, motors):
            # raise DeprecationWarning
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
        def get_available_records2():
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

        @self.app.get('/detect/<marker>')
        def detect_marker(marker):
            markers = {
                'tetris': [112259237],
                'caribou': [221052793],
                'lapin': [44616414],
                'rabbit': [44616414],
            }
            try:
                detected = rr.robot.marker_detector.markers
                return str(any([m.id in markers[marker] for m in detected]))
            except AttributeError:
                return 'Error: marker detector is not activated'

        @self.app.get('/ik/<chain>/endeffector')
        def ik_endeffector(chain):
            c = getattr(rr.robot, chain)
            pos = list(numpy.round(c.end_effector, 4))
            return ','.join(map(str, pos))

        @self.app.get('/ik/<chain>/goto/<x>/<y>/<z>/<duration>')
        def ik_goto(chain, x, y, z, duration):
            c = getattr(rr.robot, chain)
            c.goto([x, y, z], duration, wait=False)
            return "Done !"

    def run(self, quiet=None, server=''):
        """ Start the tornado server, run forever.
            'quiet' and 'server' arguments are no longer used, they are keep only for backward compatibility
        """

        try:
            loop = IOLoop()
            http_server = HTTPServer(WSGIContainer(self.app))
            http_server.listen(self.port)
            loop.start()

        except socket.error as serr:
            # Re raise the socket error if not "[Errno 98] Address already in use"
            if serr.errno != errno.EADDRINUSE:
                raise serr
            else:
                logger.warning("""The webserver port {} is already used.
The SnapRobotServer is maybe already run or another software use this port.""".format(self.port))

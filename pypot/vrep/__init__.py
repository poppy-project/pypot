from .controller import VrepController


from ..dynamixel.motor import DxlAXRXMotor, DxlMXMotor
from ..robot.config import _motor_extractor

from ..robot import Robot

from threading import Thread


def from_vrep(vrep_host, vrep_port, config):
    class VrepRobot(Robot):
        def __init__(self, vrep_host, vrep_port, config):
            Robot.__init__(self)

            self._motors.extend(bob(config))
            for m in self._motors:
                m.goal_position = 0.0

            for m in self._motors:
                setattr(self, m.name, m)

            alias = config['motorgroups']
            for alias_name in alias:
                motors = [getattr(self, name)
                            for name in _motor_extractor(alias, alias_name)]
                setattr(self, alias_name, motors)
                self.alias.append(alias_name)


            self.vrep_controller = VrepController(vrep_host, vrep_port, self._motors)

            self.safe_start()

            self.t = Thread(target=self._sync)
            self.t.start()

        def safe_start(self):
            for m in self._motors:
                while True:
                    try:
                        self.vrep_controller._set_motor_position(motor_name=m.name,
                                                                 position=0.0)
                        break
                    except:
                        pass

        def _sync(self):
            from numpy import deg2rad
            import time

            while True:
                for m in self._motors:
                    self.vrep_controller._set_motor_position(motor_name=m.name,
                                                         position=deg2rad(m.goal_position))
                time.sleep(0.02)

    return VrepRobot(vrep_host, vrep_port, config)


def bob(config):
    dxl_motors = []

    alias = config['motorgroups']

    for c_name, c_params in config['controllers'].items():
        motor_names = sum([_motor_extractor(alias, name)
                           for name in c_params['attached_motors']], [])
        motor_nodes = map(lambda m: (m, config['motors'][m]), motor_names)

        # Instatiate the attached motors and set their angle_limits if needed
        for m_name, m_params in motor_nodes:
            MotorCls = DxlMXMotor if m_params['type'].startswith('MX') else DxlAXRXMotor

            m = MotorCls(id=m_params['id'],
                         name=m_name,
                         direct=True if m_params['orientation'] == 'direct' else False,
                         offset=m_params['offset'])

            dxl_motors.append(m)

    return dxl_motors

import itertools

from .abstract_io import (AbstractDxlIO, _DxlControl,
                          _DxlAccess, DxlTimeoutError)
from .. import conversion as conv
from ..protocol import v1 as v1


class DxlIO(AbstractDxlIO):
    _protocol = v1

    def factory_reset(self):
        """ Reset all motors on the bus to their factory default settings. """
        try:
            self._send_packet(self._protocol.DxlResetPacket())

        except DxlTimeoutError:
            pass

    def get_control_mode(self, ids):
        """ Gets the mode ('joint' or 'wheel') for the specified motors. """
        to_get_ids = [id for id in ids if id not in self._known_mode]
        limits = self.get_angle_limit(to_get_ids, convert=False)
        modes = ['wheel' if limit == (0, 0) else 'joint' for limit in limits]

        self._known_mode.update(zip(to_get_ids, modes))

        return tuple(self._known_mode[id] for id in ids)

    def set_wheel_mode(self, ids):
        """ Sets the specified motors to wheel mode. """
        self.set_control_mode(dict(zip(ids, itertools.repeat('wheel'))))

    def set_joint_mode(self, ids):
        """ Sets the specified motors to joint mode. """
        self.set_control_mode(dict(zip(ids, itertools.repeat('joint'))))

    def set_control_mode(self, mode_for_id):
        models = []
        for m in self.get_model(list(mode_for_id.keys())):
            if m.startswith('MX'):
                models += ['MX']
            elif m.startswith('SR'):
                models += ['SR']
            else:
                models += ['*']

        pos_max = [conv.position_range[m][0] for m in models]
        limits = ((0, 0) if mode == 'wheel' else (0, pos_max[i] - 1)
                  for i, mode in enumerate(mode_for_id.itervalues()))

        self._set_angle_limit(dict(zip(mode_for_id.keys(), limits)), convert=False)
        self._known_mode.update(mode_for_id.items())

    def set_angle_limit(self, limit_for_id, **kwargs):
        """ Sets the angle limit to the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert

        if 'wheel' in self.get_control_mode(limit_for_id.keys()):
            raise ValueError('can not change the angle limit of a motor in wheel mode')

        if (0, 0) in limit_for_id.values():
            raise ValueError('can not set limit to (0, 0)')

        self._set_angle_limit(limit_for_id, convert=convert)

# MARK: - Generate the accessors


def _add_control(name,
                 address, length=2, nb_elem=1,
                 access=_DxlAccess.readwrite,
                 models=set(conv.dynamixelModels.values()),
                 dxl_to_si=lambda val, model: val,
                 si_to_dxl=lambda val, model: val,
                 getter_name=None,
                 setter_name=None):

    control = _DxlControl(name,
                          address, length, nb_elem,
                          access,
                          models,
                          dxl_to_si, si_to_dxl,
                          getter_name, setter_name)

    DxlIO._generate_accessors(control)


_add_control('model',
             address=0x00,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_model)

_add_control('firmware',
             address=0x02, length=1,
             access=_DxlAccess.readonly)

_add_control('id',
             address=0x03, length=1,
             access=_DxlAccess.writeonly,
             setter_name='change_id')

_add_control('baudrate',
             address=0x04, length=1,
             access=_DxlAccess.writeonly,
             setter_name='change_baudrate',
             si_to_dxl=conv.baudrate_to_dxl)

_add_control('return delay time',
             address=0x05, length=1,
             dxl_to_si=conv.dxl_to_rdt,
             si_to_dxl=conv.rdt_to_dxl)

_add_control('angle limit',
             address=0x06, nb_elem=2,
             dxl_to_si=lambda value, model: (conv.dxl_to_degree(value[0], model),
                                             conv.dxl_to_degree(value[1], model)),
             si_to_dxl=lambda value, model: (conv.degree_to_dxl(value[0], model),
                                             conv.degree_to_dxl(value[1], model)))

_add_control('drive mode',
             address=0x0A, length=1,
             access=_DxlAccess.readwrite,
             models=('MX-106', ),
             dxl_to_si=conv.dxl_to_drive_mode,
             si_to_dxl=conv.drive_mode_to_dxl)

_add_control('highest temperature limit',
             address=0x0B, length=1,
             dxl_to_si=conv.dxl_to_temperature,
             si_to_dxl=conv.temperature_to_dxl)

_add_control('voltage limit',
             address=0x0C, length=1, nb_elem=2,
             dxl_to_si=lambda value, model: (conv.dxl_to_voltage(value[0], model),
                                             conv.dxl_to_voltage(value[1], model)),
             si_to_dxl=lambda value, model: (conv.voltage_to_dxl(value[0], model),
                                             conv.voltage_to_dxl(value[1], model)))

_add_control('max torque',
             address=0x0E,
             dxl_to_si=conv.dxl_to_torque,
             si_to_dxl=conv.torque_to_dxl)

_add_control('status return level',
             address=0x10, length=1,
             dxl_to_si=conv.dxl_to_status,
             si_to_dxl=conv.status_to_dxl)

_add_control('alarm LED',
             address=0x11, length=1,
             dxl_to_si=conv.dxl_to_alarm,
             si_to_dxl=conv.alarm_to_dxl)

_add_control('alarm shutdown',
             address=0x12, length=1,
             dxl_to_si=conv.dxl_to_alarm,
             si_to_dxl=conv.alarm_to_dxl)

_add_control('torque_enable',
             address=0x18, length=1,
             dxl_to_si=conv.dxl_to_bool,
             si_to_dxl=conv.bool_to_dxl,
             getter_name='is_torque_enabled',
             setter_name='_set_torque_enable')

_add_control('LED',
             address=0x19, length=1,
             dxl_to_si=conv.dxl_to_bool,
             si_to_dxl=conv.bool_to_dxl,
             setter_name='_set_LED',
             getter_name='is_led_on')

_add_control('pid gain',
             address=0x1A, length=1, nb_elem=3,
             models=('MX-12', 'MX-28', 'MX-64', 'MX-106'),
             dxl_to_si=conv.dxl_to_pid,
             si_to_dxl=conv.pid_to_dxl)

_add_control('compliance margin',
             address=0x1A, length=1, nb_elem=2,
             models=('AX-12', 'AX-18', 'RX-24', 'RX-28', 'RX-64'))

_add_control('compliance slope',
             address=0x1C, length=1, nb_elem=2,
             models=('AX-12', 'AX-18', 'RX-24', 'RX-28', 'RX-64'))

_add_control('goal position',
             address=0x1E,
             dxl_to_si=conv.dxl_to_degree,
             si_to_dxl=conv.degree_to_dxl)

_add_control('moving speed',
             address=0x20,
             dxl_to_si=conv.dxl_to_speed,
             si_to_dxl=conv.speed_to_dxl)

_add_control('torque limit',
             address=0x22,
             dxl_to_si=conv.dxl_to_torque,
             si_to_dxl=conv.torque_to_dxl)

_add_control('goal position speed load',
             address=0x1E, nb_elem=3,
             dxl_to_si=lambda value, model: (conv.dxl_to_degree(value[0], model),
                                             conv.dxl_to_speed(value[1], model),
                                             conv.dxl_to_load(value[2], model)),
             si_to_dxl=lambda value, model: (conv.degree_to_dxl(value[0], model),
                                             conv.speed_to_dxl(value[1], model),
                                             conv.torque_to_dxl(value[2], model)))

_add_control('present position',
             address=0x24,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_degree)

_add_control('present speed',
             address=0x26,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_speed)

_add_control('present load',
             address=0x28,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_load)

_add_control('present position speed load',
             address=0x24, nb_elem=3,
             access=_DxlAccess.readonly,
             dxl_to_si=lambda value, model: (conv.dxl_to_degree(value[0], model),
                                             conv.dxl_to_speed(value[1], model),
                                             conv.dxl_to_load(value[2], model)))

_add_control('present voltage',
             address=0x2A, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_voltage)

_add_control('present temperature',
             address=0x2B, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_temperature)

_add_control('moving',
             address=0x2E, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=conv.dxl_to_bool,
             getter_name='is_moving')

_add_control('punch',
             address=0x30, length=2,
             models=('AX-12', 'AX-18', 'RX-24', 'RX-28', 'RX-64'))

_add_control('present current',
             address=0x44,
             access=_DxlAccess.readonly,
             models=('MX-64', 'MX-106', 'SR-RH4D',),
             dxl_to_si=conv.dxl_to_current)

_add_control('force control enable',
             address=0x46, length=1,
             models=('SR-RH4D',),
             dxl_to_si=conv.dxl_to_bool,
             si_to_dxl=conv.bool_to_dxl)

_add_control('goal force',
             address=0x47,
             models=('SR-RH4D',))

_add_control('goal acceleration',
             address=0x49, length=1,
             models=('MX-12, MX-28', 'MX-64', 'MX-106'),
             dxl_to_si=conv.dxl_to_acceleration,
             si_to_dxl=conv.acceleration_to_dxl)

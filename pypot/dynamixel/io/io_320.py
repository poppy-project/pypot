from itertools import repeat

from .abstract_io import (AbstractDxlIO, _DxlControl,
                          _DxlAccess, DxlTimeoutError)
from .. import conversion as conv
from ..protocol import v2 as v2


class Dxl320IO(AbstractDxlIO):
    _protocol = v2

    def set_wheel_mode(self, ids):
        self.set_control_mode(dict(zip(ids, repeat('wheel'))))

    def set_joint_mode(self, ids):
        self.set_control_mode(dict(zip(ids, repeat('joint'))))

    def get_goal_position_speed_load(self, ids):
        a = self._get_goal_pos_speed(ids)
        b = self.get_torque_limit(ids)

        return zip(*zip(*a) + [b])

    def set_goal_position_speed_load(self, value_for_ids):
        values = zip(*value_for_ids.values())

        self._set_goal_pos_speed(dict(zip(value_for_ids.keys(),
                                          zip(*(values[0], values[1])))))

        self.set_torque_limit(dict(zip(value_for_ids.keys(), values[2])))

    def factory_reset(self, ids, except_ids=False, except_baudrate_and_ids=False):
        """ Reset all motors on the bus to their factory default settings. """

        mode = (0x02 if except_baudrate_and_ids else
                0x01 if except_ids else 0xFF)

        for id in ids:
            try:
                self._send_packet(self._protocol.DxlResetPacket(id, mode))

            except DxlTimeoutError:
                pass

# TODO:
#   * error

# MARK: - Generate the accessors


controls = {
    # EEPROM
    'model': {
        'address': 0x00,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_model
    },
    'firmware': {
        'address': 0x02,
        'length': 1,
        'access': _DxlAccess.readonly
    },
    'id': {
        'address': 0x03,
        'length': 1,
        'access': _DxlAccess.writeonly,
        'setter_name': 'change_id'
    },
    'baudrate': {
        'address': 0x04,
        'length': 1,
        'access': _DxlAccess.writeonly,
        'setter_name': 'change_baudrate',
        'si_to_dxl': conv.baudrate_to_dxl
    },
    'return delay time': {
        'address': 0x05,
        'length': 1,
        'dxl_to_si': conv.dxl_to_rdt,
        'si_to_dxl': conv.rdt_to_dxl
    },
    'angle limit': {
        'address': 0x06,
        'nb_elem': 2,
        'dxl_to_si': lambda value, model: (conv.dxl_to_degree(value[0], model),
                                           conv.dxl_to_degree(value[1], model)),
        'si_to_dxl': lambda value, model: (conv.degree_to_dxl(value[0], model),
                                           conv.degree_to_dxl(value[1], model))
    },
    'control mode': {
        'address': 0x0B,
        'length': 1,
        'dxl_to_si': conv.dxl_to_control_mode,
        'si_to_dxl': conv.control_mode_to_dxl,
    },
    'highest temperature limit': {
        'address': 0x0C,
        'length': 1,
        'dxl_to_si': conv.dxl_to_temperature,
        'si_to_dxl': conv.temperature_to_dxl
    },
    'voltage limit': {
        'address': 0x0D,
        'length': 1,
        'nb_elem': 2,
        'dxl_to_si': lambda value, model: (conv.dxl_to_voltage(value[0], model),
                                           conv.dxl_to_voltage(value[1], model)),
        'si_to_dxl': lambda value, model: (conv.voltage_to_dxl(value[0], model),
                                           conv.voltage_to_dxl(value[1], model))
    },
    'max torque': {
        'address': 0x0F,
        'dxl_to_si': conv.dxl_to_torque,
        'si_to_dxl': conv.torque_to_dxl
    },
    'status return level': {
        'address': 0x11,
        'length': 1,
        'dxl_to_si': conv.dxl_to_status,
        'si_to_dxl': conv.status_to_dxl
    },
    'alarm shutdown': {
        'address': 0x12,
        'length': 1,
        'dxl_to_si': conv.dxl_to_alarm,
        'si_to_dxl': conv.alarm_to_dxl
    },
    # RAM
    'torque_enable': {
        'address': 0x18,
        'length': 1,
        'dxl_to_si': conv.dxl_to_bool,
        'si_to_dxl': conv.bool_to_dxl,
        'getter_name': 'is_torque_enabled',
        'setter_name': '_set_torque_enable'
    },
    'LED': {
        'address': 0x19,
        'length': 1,
        'dxl_to_si': conv.dxl_to_bool,
        'si_to_dxl': conv.bool_to_dxl,
        'setter_name': '_set_LED',
        'getter_name': 'is_led_on'
    },
    'LED color': {
        'address': 0x19,
        'length': 1,
        'dxl_to_si': conv.dxl_to_led_color,
        'si_to_dxl': conv.led_color_to_dxl,
    },
    'pid gain': {
        'address': 0x1B,
        'length': 1,
        'nb_elem': 3,
        'dxl_to_si': conv.dxl_to_pid,
        'si_to_dxl': conv.pid_to_dxl
    },
    'goal position': {
        'address': 0x1E,
        'dxl_to_si': conv.dxl_to_degree,
        'si_to_dxl': conv.degree_to_dxl
    },
    'moving speed': {
        'address': 0x20,
        'dxl_to_si': conv.dxl_to_speed,
        'si_to_dxl': conv.speed_to_dxl
    },
    'torque limit': {
        'address': 0x23,
        'dxl_to_si': conv.dxl_to_torque,
        'si_to_dxl': conv.torque_to_dxl
    },
    'goal position speed': {
        'address': 0x1E,
        'nb_elem': 2,
        'dxl_to_si': lambda value, model: (conv.dxl_to_degree(value[0], model),
                                           conv.dxl_to_speed(value[1], model)),
        'si_to_dxl': lambda value, model: (conv.degree_to_dxl(value[0], model),
                                           conv.speed_to_dxl(value[1], model)),
        'getter_name': '_get_goal_pos_speed',
        'setter_name': '_set_goal_pos_speed'
    },
    'present position': {
        'address': 0x25,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_degree
    },
    'present speed': {
        'address': 0x27,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_speed
    },
    'present load': {
        'address': 0x29,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_load
    },
    'present position speed load': {
        'address': 0x25,
        'nb_elem': 3,
        'access': _DxlAccess.readonly,
        'dxl_to_si': lambda value, model: (conv.dxl_to_degree(value[0], model),
                                           conv.dxl_to_speed(value[1], model),
                                           conv.dxl_to_load(value[2], model))
    },
    'present voltage': {
        'address': 0x2D,
        'length': 1,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_voltage
    },
    'present temperature': {
        'address': 0x2E,
        'length': 1,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_temperature
    },
    'moving': {
        'address': 0x31,
        'length': 1,
        'access': _DxlAccess.readonly,
        'dxl_to_si': conv.dxl_to_bool,
        'getter_name': 'is_moving'
    }
}


def _add_control(name,
                 address, length=2, nb_elem=1,
                 access=_DxlAccess.readwrite,
                 models=['XL-320', ],
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

    Dxl320IO._generate_accessors(control)

for name, args in controls.items():
    _add_control(name, **args)

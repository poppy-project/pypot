from .abstract_io import (AbstractDxlIO, _DxlControl,
                          _DxlAccess, DxlTimeoutError)
from ..protocol import v1 as v1
from ..conversion import *


class DxlIO(AbstractDxlIO):
    _protocol = v1

    def factory_reset(self):
        """ Reset all motors on the bus to their factory default settings. """
        try:
            self._send_packet(self._protocol.DxlResetPacket())

        except DxlTimeoutError:
            pass

# MARK: - Generate the accessors


def _add_control(name,
                 address, length=2, nb_elem=1,
                 access=_DxlAccess.readwrite,
                 models=set(dynamixelModels.values()),
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
             dxl_to_si=dxl_to_model)

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
             si_to_dxl=baudrate_to_dxl)

_add_control('return delay time',
             address=0x05, length=1,
             dxl_to_si=dxl_to_rdt,
             si_to_dxl=rdt_to_dxl)

_add_control('angle limit',
             address=0x06, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_degree(value[1], model)),
             si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                             degree_to_dxl(value[1], model)))

_add_control('drive mode',
             address=0x0A, length=1,
             access=_DxlAccess.readwrite,
             models=('MX-106', ),
             dxl_to_si=dxl_to_drive_mode,
             si_to_dxl=drive_mode_to_dxl)

_add_control('highest temperature limit',
             address=0x0B, length=1,
             dxl_to_si=dxl_to_temperature,
             si_to_dxl=temperature_to_dxl)

_add_control('voltage limit',
             address=0x0C, length=1, nb_elem=2,
             dxl_to_si=lambda value, model: (dxl_to_voltage(value[0], model),
                                             dxl_to_voltage(value[1], model)),
             si_to_dxl=lambda value, model: (voltage_to_dxl(value[0], model),
                                             voltage_to_dxl(value[1], model)))

_add_control('max torque',
             address=0x0E,
             dxl_to_si=dxl_to_torque,
             si_to_dxl=torque_to_dxl)

_add_control('status return level',
             address=0x10, length=1,
             dxl_to_si=dxl_to_status,
             si_to_dxl=status_to_dxl)

_add_control('alarm LED',
             address=0x11, length=1,
             dxl_to_si=dxl_to_alarm,
             si_to_dxl=alarm_to_dxl)

_add_control('alarm shutdown',
             address=0x12, length=1,
             dxl_to_si=dxl_to_alarm,
             si_to_dxl=alarm_to_dxl)

_add_control('torque_enable',
             address=0x18, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl,
             getter_name='is_torque_enabled',
             setter_name='_set_torque_enable')

_add_control('LED',
             address=0x19, length=1,
             dxl_to_si=dxl_to_bool,
             si_to_dxl=bool_to_dxl,
             setter_name='_set_LED',
             getter_name='is_led_on')

_add_control('pid gain',
             address=0x1A, length=1, nb_elem=3,
             models=('MX-12', 'MX-28', 'MX-64', 'MX-106'),
             dxl_to_si=dxl_to_pid,
             si_to_dxl=pid_to_dxl)

_add_control('compliance margin',
             address=0x1A, length=1, nb_elem=2,
             models=('AX-12', 'AX-18', 'RX-28', 'RX-64'))

_add_control('compliance slope',
             address=0x1C, length=1, nb_elem=2,
             models=('AX-12', 'AX-18', 'RX-28', 'RX-64'))

_add_control('goal position',
             address=0x1E,
             dxl_to_si=dxl_to_degree,
             si_to_dxl=degree_to_dxl)

_add_control('moving speed',
             address=0x20,
             dxl_to_si=dxl_to_speed,
             si_to_dxl=speed_to_dxl)

_add_control('torque limit',
             address=0x22,
             dxl_to_si=dxl_to_torque,
             si_to_dxl=torque_to_dxl)

_add_control('goal position speed load',
             address=0x1E, nb_elem=3,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_speed(value[1], model),
                                             dxl_to_load(value[2], model)),
             si_to_dxl=lambda value, model: (degree_to_dxl(value[0], model),
                                             speed_to_dxl(value[1], model),
                                             torque_to_dxl(value[2], model)))

_add_control('present position',
             address=0x24,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_degree)

_add_control('present speed',
             address=0x26,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_speed)

_add_control('present load',
             address=0x28,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_load)

_add_control('present position speed load',
             address=0x24, nb_elem=3,
             access=_DxlAccess.readonly,
             dxl_to_si=lambda value, model: (dxl_to_degree(value[0], model),
                                             dxl_to_speed(value[1], model),
                                             dxl_to_load(value[2], model)))

_add_control('present voltage',
             address=0x2A, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_voltage)

_add_control('present temperature',
             address=0x2B, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_temperature)

_add_control('moving',
             address=0x2E, length=1,
             access=_DxlAccess.readonly,
             dxl_to_si=dxl_to_bool,
             getter_name='is_moving')

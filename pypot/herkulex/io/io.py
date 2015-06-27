from .abstract_io import (AbstractHkxIO, _HkxControl,
                          _HkxAccess, HkxTimeoutError)
from ..protocol import *
from ..conversion import *


class HkxIO(AbstractHkxIO):


    def factory_reset(self):
        """ Reset all motors on the bus to their factory default settings. """
        try:
            self._send_packet(HkxRollBackPacket())

        except HkxTimeoutError:
            pass
        
    #TODO: functions to set wheel and joint modes

    def set_angle_limit(self, limit_for_id, **kwargs):
        """ Sets the angle limit to the specified motors. """
        convert = kwargs['convert'] if 'convert' in kwargs else self._convert
        #TODO: check if there are requirements before changing angle limits
        self._set_angle_limit(limit_for_id, convert=convert)
        
    def get_goal_position_load(self, ids, **kwargs):
        pos = self.get_goal_position(ids)
        ld = self.get_torque_limit(ids)
        return (pos,ld)

    def set_joint_jog_load(self, input_dict):
        nid = input_dict.keys()
        nval = [(d[0], d[1], 'off') for d in input_dict.values()]
        jointjog=dict(list(zip(nid,nval)))
        self.joint_jog(jointjog, convert = True)


# MARK: - Generate the accessors

def _add_control(name, eeprom_ram,
                 address, length=2, nb_elem=1,
                 access=_HkxAccess.readwrite,
                 models=set(herkulexModels.values()),
                 hkx_to_si=lambda val, model: val,
                 si_to_hkx=lambda val, model: val,
                 getter_name=None,
                 setter_name=None):

    control = _HkxControl(name, eeprom_ram,
                          address, length, nb_elem,
                          access,
                          models,
                          hkx_to_si, si_to_hkx,
                          getter_name, setter_name)

    HkxIO._generate_accessors(control)


_add_control('model',
             eeprom_ram = 'EEPROM',
             address=0,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_model)

_add_control('firmware',
             eeprom_ram = 'EEPROM',           
             address=2,
             access=_HkxAccess.readonly)
             
_add_control('baudrate',
             eeprom_ram = 'EEPROM',  
             address=4, length=1,
             access=_HkxAccess.writeonly,
             setter_name='change_baudrate',
             si_to_hkx=baudrate_to_hkx)

_add_control('id_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=6, length=1,
             access=_HkxAccess.writeonly,
             setter_name='change_id_EEPROM')

_add_control('id',
             eeprom_ram = 'RAM', 
             address=0, length=1,
             access=_HkxAccess.writeonly,
             setter_name='change_id')

_add_control('highest_temperature_limit_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=11, length=1,
             hkx_to_si=hkx_to_temperature,
             si_to_hkx=temperature_to_hkx)

_add_control('highest_temperature_limit',
             eeprom_ram = 'RAM', 
             address=5, length=1,
             hkx_to_si=hkx_to_temperature,
             si_to_hkx=temperature_to_hkx)

_add_control('voltage_limit_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=12, length=1, nb_elem=2,
             hkx_to_si=lambda value, model: (hkx_to_voltage(value[0], model),
                                             hkx_to_voltage(value[1], model)),
             si_to_hkx=lambda value, model: (voltage_to_hkx(value[0], model),
                                             voltage_to_hkx(value[1], model)))

_add_control('voltage_limit',
             eeprom_ram = 'RAM', 
             address=6, length=1, nb_elem=2,
             hkx_to_si=lambda value, model: (hkx_to_voltage(value[0], model),
                                             hkx_to_voltage(value[1], model)),
             si_to_hkx=lambda value, model: (voltage_to_hkx(value[0], model),
                                             voltage_to_hkx(value[1], model)))

_add_control('accel_ratio',
             eeprom_ram = 'RAM', 
             address=8, length=1,
             si_to_hkx=accel_ratio_to_hkx)

_add_control('accel_ratio_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=14, length=1,
             si_to_hkx=accel_ratio_to_hkx)

_add_control('max_accel_time',
             eeprom_ram = 'RAM', 
             address=9, length=1,
             hkx_to_si=hkx_to_time,
             si_to_hkx=time_to_hkx)

_add_control('max_accel_time_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=15, length=1,
             hkx_to_si=hkx_to_time,
             si_to_hkx=time_to_hkx)

_add_control('compliance_margin_EPPROM',
             address=16, length=1,
             eeprom_ram = 'EEPROM')

_add_control('compliance_margin',
             address=10, length=1,
             eeprom_ram = 'RAM')

_add_control('compliance_slope_EEPROM',
             address=18,
             eeprom_ram = 'EEPROM')

_add_control('compliance_slope',
             address=12,
             eeprom_ram = 'RAM')
             
_add_control('torque_limit_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=22,
             hkx_to_si=hkx_to_torque,
             si_to_hkx=torque_to_hkx)

_add_control('torque_limit',
             eeprom_ram = 'RAM', 
             address=16,
             hkx_to_si=hkx_to_torque,
             si_to_hkx=torque_to_hkx)

_add_control('angle_limit_EEPROM',
             eeprom_ram = 'EEPROM', 
             address=26, nb_elem=2,
             hkx_to_si=lambda value, model: (hkx_to_degree(value[0], model),
                                             hkx_to_degree(value[1], model)),
             si_to_hkx=lambda value, model: (degree_to_hkx(value[0], model),
                                             degree_to_hkx(value[1], model)))
                                             
_add_control('angle_limit',
             eeprom_ram = 'RAM', 
             address=20, nb_elem=2,
             hkx_to_si=lambda value, model: (hkx_to_degree(value[0], model),
                                             hkx_to_degree(value[1], model)),
             si_to_hkx=lambda value, model: (degree_to_hkx(value[0], model),
                                             degree_to_hkx(value[1], model)),
             setter_name='_set_angle_limit')

_add_control('status_error',
             eeprom_ram = 'RAM', 
             address=48, length=1,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_status_error)

_add_control('status_detail',
             eeprom_ram = 'RAM', 
             address=49, length=1,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_status_detail)

_add_control('torque_enable',
             eeprom_ram = 'RAM', 
             address=52, length=1,
             hkx_to_si=hkx_to_torque_enabled,
             si_to_hkx=torque_enabled_to_hkx,
             getter_name='is_torque_enabled',
             setter_name='_set_torque_enable')

_add_control('LED',
             eeprom_ram = 'RAM', 
             address=53, length=1,
             hkx_to_si=hkx_to_LED,
             si_to_hkx=LED_to_hkx)
             
_add_control('present_voltage',
             eeprom_ram = 'RAM', 
             address=54, length=1,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_voltage)

_add_control('present_temperature',
             eeprom_ram = 'RAM', 
             address=55, length=1,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_temperature)

_add_control('control_mode',
             eeprom_ram = 'RAM', 
             address=56, length=1,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_control_mode,
             si_to_hkx=control_mode_to_hkx)


_add_control('present_position',
             eeprom_ram = 'RAM', 
             address=60,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_degree)
             
_add_control('present_speed',
             eeprom_ram = 'RAM', 
             address=62,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_speed)

_add_control('present_load',
             eeprom_ram = 'RAM', 
             address=64,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_load)
             
_add_control('goal_position',
             eeprom_ram = 'RAM', 
             address=68,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_degree)

_add_control('local_goal_position',
             eeprom_ram = 'RAM', 
             address=70,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_degree)

_add_control('local_goal_speed',
             eeprom_ram = 'RAM', 
             address=72,
             access=_HkxAccess.readonly,
             hkx_to_si=hkx_to_speed)
             
_add_control('present_position_speed_load',
             eeprom_ram = 'RAM',
             address=60, nb_elem=3,
             access=_HkxAccess.readonly,
             hkx_to_si=lambda value, model: (hkx_to_degree(value[0], model),
                                             hkx_to_speed(value[1], model),
                                             hkx_to_load(value[2], model)))

_add_control('present_voltage_temperature',
             eeprom_ram = 'RAM',
             address=54, nb_elem=2,
             access=_HkxAccess.readonly,
             hkx_to_si=lambda value, model: (hkx_to_voltage(value[0], model),
                                             hkx_to_temperature(value[1], model)))


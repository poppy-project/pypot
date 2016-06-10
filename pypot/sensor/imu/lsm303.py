import numpy
import math
import time

from collections import namedtuple

from ...utils.i2c_controller import I2cController
from .kalman_filter import KalmanFilter
from ...utils import StoppableThread
from ...robot.sensor import Sensor


Orientation = namedtuple('Orientation', 'roll pitch yaw')


class IMUSensor(Sensor):
    """ IMU sensor class, it provides an orientation (roll, pitch, yaw). """
    registers = Sensor.registers + ['orientation']

    def __init__(self, name, i2c_pin):
        Sensor.__init__(self, name)

        self._imu = IMU(i2c_pin)
        self._imu.start()

    def close(self):
        self._imu.stop()

    @property
    def orientation(self):
        return self._imu.get_orientation()


class IMU(StoppableThread):
    DELAY_TIME = 0.02
    GYRO_NOISE = 0.001
    BIAS_NOISE = 0.003
    ACCEL_NOISE = 0.01

    def __init__(self, i2c_bus=1):
        StoppableThread.__init__(self, target=self.update_orientation)

        self.gyro = L3GD20Gyroscope(i2c_bus, L3GD20Gyroscope.DPS2000)
        self.accel = LSM303Accelerometer(i2c_bus, LSM303Accelerometer.SCALE_A_8G)

        self.roll, self.pitch, self.yaw = self.accel.get_orientation()

        self.kalman_filter = KalmanFilter(IMU.GYRO_NOISE,
                                          IMU.BIAS_NOISE,
                                          IMU.ACCEL_NOISE)

    def zero(self):
        self.gyro.zero()
        self.accel.zero()

    def update_orientation(self):
        self.elapsed_time = IMU.DELAY_TIME

        while not self.should_stop():
            start_time = time.time()

            gyro_x, gyro_y, gyro_z = self.gyro.get_raw_data()
            roll, pitch, _ = self.accel.get_orientation()

            self.roll = self.kalman_filter.filterX(roll, gyro_x, self.elapsed_time)
            self.pitch = self.kalman_filter.filterY(pitch, gyro_y, self.elapsed_time)

            if abs(gyro_x) > 0.5:
                self.roll += (gyro_x * self.elapsed_time)

            if abs(gyro_y) > 0.5:
                self.pitch += (gyro_y * self.elapsed_time)

            if abs(gyro_z) > 0.5:
                self.yaw += (gyro_z * self.elapsed_time)

            # complementary filter
            self.roll = self.roll * 0.95 + roll * 0.05
            self.pitch = self.pitch * 0.95 + pitch * 0.05

            # low pass filter
            self.roll = self.roll * 0.5 + roll * 0.5
            self.pitch = self.pitch * 0.5 + pitch * 0.5

            time.sleep(max(0, IMU.DELAY_TIME - (time.time() - start_time)))
            self.elapsed_time = time.time() - start_time

    def get_orientation(self):
        return Orientation(self.roll, self.pitch, self.yaw)


class LSM303Accelerometer(object):
    """ Accelerometer + magnetometer sensor. """

    LSM_ACC_ADDR = 0x19

    CTRL_REG1_A = 0x20
    CTRL_REG4_A = 0x23
    OUT_X_L_A = 0x28
    OUT_X_H_A = 0x29
    OUT_Y_L_A = 0x2A
    OUT_Y_H_A = 0x2B
    OUT_Z_L_A = 0x2C
    OUT_Z_H_A = 0x2D

    POWER_ON = 0b10010111       # ON LSM303Accelerometer ACC. and 1.344 KHz mode
    SCALE_A_2G = 0b00001000     # +/- 2 G scale, and HR
    SCALE_A_4G = 0b00011000     # +/- 4 G scale, and HR
    SCALE_A_8G = 0b00101000     # +/- 8 G scale, and HR
    SCALE_A_16G = 0b00111000  # +/-16 G scale, and HR

    LSM_MAG_ADDR = 0x1E

    CRA_REG_M = 0x00
    CRB_REG_M = 0x01
    MR_REG_M = 0x02
    OUT_X_L_M = 0x03
    OUT_X_H_M = 0x04
    OUT_Y_L_M = 0x05
    OUT_Y_H_M = 0x06
    OUT_Z_L_M = 0x07
    OUT_Z_H_M = 0x08

    DATA_RATE = 0b00011000  # Temp. Sen. Disable and 75H output rate
    CONV_MODE = 0b00000000  # Continuous conversion mode

    SCALE_M_13G = 0b00100000  # +/- 1.3 Gauss scale
    SCALE_M_19G = 0b01000000  # +/- 1.9 Gauss scale
    SCALE_M_25G = 0b01100000  # +/- 2.5 Gauss scale
    SCALE_M_40G = 0b10000000  # +/- 4.0 Gauss scale
    SCALE_M_47G = 0b10100000  # +/- 4.7 Gauss scale
    SCALE_M_56G = 0b11000000  # +/- 5.6 Gauss scale
    SCALE_M_81G = 0b11100000  # +/- 8.1 Gauss scale

    ZERO_X = -73
    ZERO_Y = 37
    ZERO_Z = -63
    # 73.312 -36.512 4102.48

    def __init__(self, i2c_bus, gauss_scale):
        self.bus = I2cController(i2c_bus)
        self.bus.write_byte_data(
            LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.CTRL_REG1_A, LSM303Accelerometer.POWER_ON)
        self.bus.write_byte_data(
            LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.CTRL_REG4_A, gauss_scale)

        if gauss_scale == LSM303Accelerometer.SCALE_A_2G:
            self.scale = (-2.0 / 32768.0)
        if gauss_scale == LSM303Accelerometer.SCALE_A_4G:
            self.scale = (-4.0 / 32768.0)
        if gauss_scale == LSM303Accelerometer.SCALE_A_8G:
            self.scale = (-8.0 / 32768.0)
        if gauss_scale == LSM303Accelerometer.SCALE_A_16G:
            self.scale = (-16.0 / 32768.0)

    def zero(self):
        count = 0
        xtotal = 0
        ytotal = 0
        ztotal = 0

        while count < 100:
            x, y, z = self.get_raw_data()
            count += 1

            xtotal = x / self.scale - self.ZERO_X + xtotal
            ytotal = y / self.scale - self.ZERO_Y + ytotal
            ztotal = z / self.scale - self.ZERO_Z + ztotal
            time.sleep(.05)

        self.ZERO_X = -1 * xtotal / 500
        self.ZERO_Y = -1 * ytotal / 500

    def get_raw_data(self):
        x = 256 * self.bus.read_byte_data(LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_X_H_A) + \
            self.bus.read_byte_data(
                LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_X_L_A)

        x = numpy.int16(x)

        y = 256 * self.bus.read_byte_data(LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Y_H_A) + \
            self.bus.read_byte_data(
                LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Y_L_A)

        y = numpy.int16(y)

        z = 256 * self.bus.read_byte_data(LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Z_H_A) + \
            self.bus.read_byte_data(
                LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Z_L_A)

        z = numpy.int16(z)
        return self.scale * (x + self.ZERO_X), self.scale * (y + self.ZERO_Y), self.scale * (z - self.ZERO_Z)

    def get_orientation(self):
        x, y, z = self.get_raw_data()

        roll = math.atan2(y, z) + math.pi
        pitch = math.atan2(x, z) + math.pi
        if roll > math.pi:
            roll = roll - 2 * math.pi
        if pitch > math.pi:
            pitch = pitch - 2 * math.pi

        return Orientation(math.degrees(roll), math.degrees(pitch), 0)


class L3GD20Gyroscope(object):
    DPS250 = 0x00  # dps: 250 (Default)
    DPS500 = 0x10  # dps: 500
    DPS2000 = 0x20  # dps: 2000

    L3GADDR = 0x6B
    CTREG1 = 0x20
    CTREG4 = 0x23

    ON = 0x0F

    XOUTLOW = 0x28
    XOUTHIGH = 0x29
    YOUTLOW = 0x2A
    YOUTHIGH = 0x2B
    ZOUTLOW = 0x2C
    ZOUTHIGH = 0x2D

    ZERO_X = -35
    ZERO_Y = 142
    ZERO_Z = -67
    # 35.17 -142.38 52.83

    def __init__(self, i2c_bus, dps):
        self.bus = I2cController(i2c_bus)
        self.bus.write_byte_data(
            L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.CTREG1, L3GD20Gyroscope.ON)
        self.bus.write_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.CTREG4, dps)
        if dps == L3GD20Gyroscope.DPS250:
            self.scale = 250.0 / 32768.0
        if dps == L3GD20Gyroscope.DPS500:
            self.scale = 500.0 / 32768.0
        if dps == L3GD20Gyroscope.DPS2000:
            self.scale = 2000.0 / 32768.0

    def zero(self):
        count = 0
        xtotal = 0
        ytotal = 0
        ztotal = 0

        while count < 100:
            x, y, z = self.get_raw_data()
            count = 1 + count
            xtotal = x / self.scale - self.ZERO_X + xtotal
            ytotal = y / self.scale - self.ZERO_Y + ytotal
            ztotal = z / self.scale - self.ZERO_Z + ztotal
            time.sleep(.075)

        self.ZERO_X = -1 * xtotal / 100
        self.ZERO_Y = -1 * ytotal / 100
        self.ZERO_Z = -1 * ztotal / 100

    def get_raw_data(self):
        x = 256 * self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.XOUTHIGH) + \
            self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.XOUTLOW)

        x = numpy.int16(x)

        y = 256 * self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.YOUTHIGH) + \
            self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.YOUTLOW)

        y = numpy.int16(y)

        z = 256 * self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.ZOUTHIGH) + \
            self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.ZOUTLOW)

        z = numpy.int16(z)

        return self.scale * (x + L3GD20Gyroscope.ZERO_X), self.scale * (y + L3GD20Gyroscope.ZERO_Y), self.scale * (z + L3GD20Gyroscope.ZERO_Z)

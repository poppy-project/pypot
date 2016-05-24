from smbus import SMBus
from bitstring import BitArray
import math
import threading
import time
from kalman_filter import *


class IMU(object):

    DELAY_TIME = .02
    GYRO_NOISE = .001
    BIAS_NOISE = .003
    ACCEL_NOISE = .01

    def __init__(self, i2cBus=1):
        self.gyro = L3GD20Gyroscope(i2cBus, L3GD20Gyroscope.DPS2000)
        self.accel = LSM303Accelerometer(i2cBus, LSM303Accelerometer.SCALE_A_8G)
        initOrientation = self.accel.get_orientation()
        self.roll = initOrientation.roll
        self.pitch = initOrientation.pitch
        self.yaw = initOrientation.yaw
        self.kalmanFilter = KalmanFilter(
            IMU.GYRO_NOISE, IMU.BIAS_NOISE, IMU.ACCEL_NOISE)
        self.thread = threading.Thread(target=self.updateOrientation)
        self.thread.daemon = True
        self.thread.start()

    def zero(self):
        self.gyro.zero()
        self.accel.zero()

    def updateOrientation(self):
        self.elapsedTime = IMU.DELAY_TIME
        while True:
            startTime = time.time()
            gyroX, gyroY, gyroZ = self.gyro.get_raw_data()
            accelOrientation = self.accel.get_orientation()

            # kalman filter
            self.roll = self.kalmanFilter.filterX(
                accelOrientation.roll, gyroX, self.elapsedTime)
            self.pitch = self.kalmanFilter.filterY(
                accelOrientation.pitch, gyroY, self.elapsedTime)

            # if abs(gyroX) > .5:
            #     self.roll = self.roll + (gyroX * self.elapsedTime)
            # if abs(gyroY) > .5:
            #     self.pitch = self.pitch - (gyroY * self.elapsedTime)
            # if abs(gyroZ) > .5:
            #     self.yaw = self.yaw + (gyroZ * self.elapsedTime)

            # # complementary filter
            # self.roll = self.roll * 0.95 + accelOrientation.roll * 0.05
            # self.pitch = self.pitch * 0.95 + accelOrientation.pitch * 0.05

            # # low pass filter
            #self.roll = self.roll*.5 + accelOrientation.roll*.5
            #self.pitch = self.pitch*.5 + accelOrientation.pitch*.5
            time.sleep(max(0, IMU.DELAY_TIME - (time.time() - startTime)))
            self.elapsedTime = time.time() - startTime

    def get_orientation(self):
        return Orientation(self.roll, self.pitch, self.yaw)


class Orientation(object):

    def __init__(self, roll, pitch, yaw):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw


class LSM303Accelerometer(object):
    """ Accelerometer + magnetometer sensor"""

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

    def __init__(self, i2cBus, gaussScale):
        self.bus = SMBus(i2cBus)
        self.bus.write_byte_data(
            LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.CTRL_REG1_A, LSM303Accelerometer.POWER_ON)
        self.bus.write_byte_data(
            LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.CTRL_REG4_A, gaussScale)

        if gaussScale == LSM303Accelerometer.SCALE_A_2G:
            self.scale = (-2.0 / 32768.0)
        if gaussScale == LSM303Accelerometer.SCALE_A_4G:
            self.scale = (-4.0 / 32768.0)
        if gaussScale == LSM303Accelerometer.SCALE_A_8G:
            self.scale = (-8.0 / 32768.0)
        if gaussScale == LSM303Accelerometer.SCALE_A_16G:
            self.scale = (-16.0 / 32768.0)

    def zero(self):
        count = 0
        xtotal = 0
        ytotal = 0
        ztotal = 0

        print 'before: ', self.ZERO_X, self.ZERO_Y, self.ZERO_Z

        while count < 100:
            x, y, z = self.get_raw_data()
            orientation = self.get_orientation()
            count = 1 + count
            print ('x = {0:.2f}, y = {1:.2f}, z = {2:.2f}').format(x, y, z)
            print ('pitch = {0:.2f}, roll = {1:.2f}').format(
                orientation.pitch, orientation.roll)
            xtotal = x / self.scale - self.ZERO_X + xtotal
            ytotal = y / self.scale - self.ZERO_Y + ytotal
            ztotal = z / self.scale - self.ZERO_Z + ztotal
            time.sleep(.05)

        self.ZERO_X = -1 * xtotal / 500
        self.ZERO_Y = -1 * ytotal / 500
        print 'after: ', self.ZERO_X, self.ZERO_Y, self.ZERO_Z

    def get_raw_data(self):
        x = 256 * self.bus.read_byte_data(LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_X_H_A) + \
            self.bus.read_byte_data(
                LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_X_L_A)
        if x >= 32768:
            x = BitArray(bin(x)).int

        y = 256 * self.bus.read_byte_data(LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Y_H_A) + \
            self.bus.read_byte_data(
                LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Y_L_A)
        if y >= 32768:
            y = BitArray(bin(y)).int

        z = 256 * self.bus.read_byte_data(LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Z_H_A) + \
            self.bus.read_byte_data(
                LSM303Accelerometer.LSM_ACC_ADDR, LSM303Accelerometer.OUT_Z_L_A)
        if z >= 32768:
            z = BitArray(bin(z)).int
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

    def __init__(self, i2cBus, dps):
        self.bus = SMBus(i2cBus)
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

        print 'before: ', self.ZERO_X, self.ZERO_Y, self.ZERO_Z

        while count < 100:
            x, y, z = self.get_raw_data()
            count = 1 + count
            print ('x = {0:.2f}, y = {1:.2f}, z = {1:.2f}').format(
                x / self.scale, y / self.scale, z / self.scale)
            xtotal = x / self.scale - self.ZERO_X + xtotal
            ytotal = y / self.scale - self.ZERO_Y + ytotal
            ztotal = z / self.scale - self.ZERO_Z + ztotal
            time.sleep(.075)

        print xtotal / 100, ytotal / 100, ztotal / 100
        self.ZERO_X = -1 * xtotal / 100
        self.ZERO_Y = -1 * ytotal / 100
        self.ZERO_Z = -1 * ztotal / 100
        print 'after: ', self.ZERO_X, self.ZERO_Y, self.ZERO_Z

    def get_raw_data(self):
        x = 256 * self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.XOUTHIGH) + \
            self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.XOUTLOW)
        if x >= 32768:
            x = BitArray(bin(x)).int

        y = 256 * self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.YOUTHIGH) + \
            self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.YOUTLOW)
        if y >= 32768:
            y = BitArray(bin(y)).int

        z = 256 * self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.ZOUTHIGH) + \
            self.bus.read_byte_data(L3GD20Gyroscope.L3GADDR, L3GD20Gyroscope.ZOUTLOW)
        if z >= 32768:
            z = BitArray(bin(z)).int

        return self.scale * (x + L3GD20Gyroscope.ZERO_X), self.scale * (y + L3GD20Gyroscope.ZERO_Y), self.scale * (z + L3GD20Gyroscope.ZERO_Z)

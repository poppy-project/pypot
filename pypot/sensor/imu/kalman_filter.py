class KalmanFilter(object):

    # A gyroscope is an electronic device that measures how many degrees per second
    # it is rotating, this is called angular rate.
    # (http://sensorwiki.org/doku.php/sensors/gyroscope)

    # Gyroscopes suffer from an effect called drift. This means that over time,
    # the value a gyroscope has when in steady position (called bias), drifts away
    # from it's initial steady value.

    # An accelerometer measures the forces acting on it including gravity and
    # motion.

    # Accelerometers suffer from noise caused by vibrations.

    # The output of the filter will be the angle but also the bias based upon the
    # measurements from the accelerometer and gyroscope. The bias is the amount
    # the gyro has drifted. This means that one can get the true rate by subtracting
    # the bias from the gyro measurement.

    # based on
    # http://blog.tkjelectronics.dk/2012/09/a-practical-approach-to-kalman-filter-and-how-to-implement-it/

    def __init__(self, gyroNoise, biasNoise, accelNoise):

        # noise constants
        self.gyroNoise = gyroNoise
        self.biasNoise = biasNoise
        self.accelNoise = accelNoise

        # error covariance matrix
        self.PX = [[0, 0], [0, 0]]
        self.PY = [[0, 0], [0, 0]]

        # bias drift
        self.biasX = 0
        self.biasY = 0

        # filtered angles
        self.filteredAngleX = 0
        self.filteredAngleY = 0

    def filterX(self, accelerometerAngleX, gyroRateX, dt):
        self.filteredAngleX, self.biasX, self.PX = self.filter(
            accelerometerAngleX, gyroRateX, dt, self.filteredAngleX, self.biasX, self.PX)
        return self.filteredAngleX

    def filterY(self, accelerometerAngleY, gyroRateY, dt):
        self.filteredAngleY, self.biasY, self.PY = self.filter(
            accelerometerAngleY, gyroRateY, dt, self.filteredAngleY, self.biasY, self.PY)
        return self.filteredAngleY

    def filter(self, accelerometerAngle, gyroRate, dt, filteredAngle, bias, P):

        # predict
        predictedAngle = filteredAngle + dt * (gyroRate - bias)
        P[0][0] = P[0][0] - dt * (P[1][0] + P[0][1]) + self.gyroNoise * dt
        P[0][1] = P[0][1] - dt * P[1][1]
        P[1][0] = P[1][0] - dt * P[1][1]
        P[1][1] = P[1][1] + self.biasNoise * dt

        # correct
        innovation = accelerometerAngle - predictedAngle
        noise = P[0][0] + self.accelNoise
        kalmanGainAngle = P[0][0] / noise
        kalmanGainBias = P[1][0] / noise

        filteredAngle = predictedAngle + kalmanGainAngle * innovation
        bias = bias + kalmanGainBias * innovation
        P[0][0] = P[0][0] - kalmanGainAngle * P[0][0]
        P[0][1] = P[0][1] - kalmanGainAngle * P[0][1]
        P[1][0] = P[1][0] - kalmanGainBias * P[0][0]
        P[1][1] = P[1][1] - kalmanGainBias * P[0][1]

        return filteredAngle, bias, P

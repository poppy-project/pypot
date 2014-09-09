import zerorpc


class RemoteRobot(object):
    def __init__(self, host, port):
        self.client = zerorpc.Client()
        self.client.connect('tcp://{}:{}'.format(host, port))

        self.motors = []

        for name in self.client.get_motors_list():
            class RemoteMotor(object):
                pass

            get = self.client.get_register_value
            set = self.client.set_register_value

            for reg in self.client.get_registers_list(name):
                setattr(RemoteMotor, reg,
                        property(lambda x: get(name, reg),
                                 lambda x, v: set(name, reg, v)))

            m = RemoteMotor()
            setattr(self, name, m)
            self.motors.append(m)


if __name__ == '__main__':
    remote_robot = RemoteRobot('127.0.0.1', 4242)

    print remote_robot.motors

    m = remote_robot.motors[0]

    print m.present_position

    from random import randint

    x = randint(0, 100)
    print 'set to', x
    m.goal_position = x

    import time
    time.sleep(1)

    print m.present_position

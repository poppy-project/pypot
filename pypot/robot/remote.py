import zerorpc


class RemoteRobotClient(object):
    """ Remote Access to a Robot through the REST API.

        This RemoteRobot gives you access to motors and alias.
        For each motor you can read/write all of their registers.

        You also have access to primitives.
        More specifically you can start/stop them.

    """
    def __init__(self, host, port):
        client = zerorpc.Client()
        client.connect('tcp://{}:{}'.format(host, port))

        self.motors = []

        for name in client.get_motors_list():
            class Register(object):
                def __init__(self, motorname, regname):
                    self.motorname = motorname
                    self.regname = regname

                def __get__(self, instance, owner):
                    return client.get_register_value(self.motorname, self.regname)

                def __set__(self, instance, value):
                    client.set_register_value(self.motorname, self.regname, value)

            class Motor(object):
                def __repr__(self):
                    return ('<Motor name={self.name} '
                            'id={self.id} '
                            'pos={self.present_position}>').format(self=self)

            for reg in client.get_registers_list(name):
                setattr(Motor, reg, Register(name, reg))

            m = Motor()
            setattr(self, m.name, m)
            self.motors.append(m)

        for alias in client.get_motors_alias():
            motors = [getattr(self, name) for name in client.get_motors_list(alias)]
            setattr(self, alias, motors)

        class Primitive(object):
            def __init__(self, name):
                self.name = name

            def start(self):
                client.start_primitive(self.name)

            def stop(self):
                client.stop_primitive(self.name)

        self.primitives = []
        for p in client.get_primitives_list():
            prim = Primitive(p)
            setattr(self, p, prim)
            self.primitives.append(prim)


def from_remote(host, port):
    """ Remote access to a Robot through the REST API. """
    return RemoteRobotClient(host, port)

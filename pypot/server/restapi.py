import os

from flask import Flask, Response, jsonify, request

from .server import AbstractServer


class RestAPIServer(AbstractServer):
    def __init__(self, robot, host, port, debug=False):
        """ Serving a robot REST API using flask.

            The documented API can be found on http://docs.pypot.apiary.io/

        """
        AbstractServer.__init__(self, robot, host, port)

        self.robot = self.restfull_robot

        self.app = Flask(__name__)  # TODO: use something better than __name__ here
        self.app.secret_key = os.urandom(24)
        self.app.debug = debug

        @self.app.route('/')
        def index():
            return Response(status=204)

        # Devices
        @self.app.route('/devices')
        def devices():
            dev_type = request.args.getlist('type')

            if not dev_type:
                dev_type = ['motor', 'sensor']

            devices = []
            for d in dev_type:
                for name in self.robot.get_devices_list('{}s'.format(d)):
                    devices.append({
                        'name': name,
                        'type': d
                    })

            return jsonify(devices=devices)

        @self.app.route('/devices/<device_name>/registers')
        def get_device_registers(device_name):
            registers = self.robot.get_device_registers_list(device_name)
            return jsonify(registers={
                reg: self.robot.get_device_register_value(device_name, reg)
                for reg in registers
            })

        @self.app.route('/devices/<device_name>/registers/<register_name>')
        def get_register_from_device(device_name, register_name):
            return jsonify(register={
                'name': register_name,
                'value': self.robot.get_device_register_value(device_name, register_name)
            })

        # Groups
        @self.app.route('/groups')
        def groups():
            groups = self.robot.get_devices_groups()
            return jsonify(
                groups=[{'name': group} for group in groups]
            )

        @self.app.route('/groups/<group_name>/registers')
        def get_group_register(group_name):
            devices = request.args.getlist('device_names')
            if not devices:
                devices = self.robot.get_devices_list(group_name)

            registers = request.args.getlist('register_names')

            # TODO: what to do if a device is not in the group
            devices = set(devices).intersection(self.robot.get_devices_list(group_name))

            answer = [{
                'name': d,
                'type': self.robot.get_device_type(d),
                'registers': {
                    reg: self.robot.get_device_register_value(d, reg)
                    for reg in (registers if registers else self.robot.get_device_registers_list(d))
                }
            } for d in devices]

            return jsonify(devices=answer)

    def run(self):
        self.app.run(self.host, self.port)

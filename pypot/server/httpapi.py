import os

from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from .server import AbstractServer


class HttpAPIServer(AbstractServer):
    def __init__(self, robot, host, port, debug=False):
        """ Serving a robot HTTP API using flask.

            The documented API can be found on http://docs.pypot.apiary.io/
            All URLs are described, with example of requests and responses.

        """
        AbstractServer.__init__(self, robot, host, port)

        self.robot = self.restfull_robot

        self.app = Flask(__name__)  # TODO: use something better than __name__ here
        self.app.secret_key = os.urandom(24)
        self.app.debug = debug
        CORS(self.app)

        # Robot's Heartbeat
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

        # Devices groups
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

        # Primitives
        @self.app.route('/primitives')
        def get_primitives():
            status = request.args.getlist('status')
            possible_status = {'running', 'stopped', 'paused'}

            # TODO: what to do if a given status is not one of the possible ones?
            status = possible_status.intersection(status)

            if not status:
                status = possible_status

            primitives = []
            for s in status:
                for p in self.robot.get_primitives_list(by_status=s):
                    primitives.append({
                        'name': p,
                        'status': s
                    })

            return jsonify(primitives=primitives)

        @self.app.route('/primitives/<primitive_name>')
        def get_primitive_information(primitive_name):
            name = primitive_name

            return jsonify(primitives={
                'name': name,
                'status': self.robot.get_primitive_property(name, 'status'),
                'description': self.robot.get_primitive_property(name, '__doc__'),
                'methods': [
                    dict(name=m)
                    for m in self.robot.get_primitive_methods_list(name)
                ],
                'properties': {
                    prop: self.robot.get_primitive_property(name, prop)
                    for prop in self.robot.get_primitive_properties_list(name)
                },
            })

        @self.app.route('/primitives/<primitive_name>/properties/<property_name>')
        def get_primitive_property(primitive_name, property_name):
            return jsonify(property={
                'name': property_name,
                'value': self.robot.get_primitive_property(primitive_name, property_name)
            })

    def run(self):
        """ Starts the server (runs for ever). """
        self.app.run(self.host, self.port)

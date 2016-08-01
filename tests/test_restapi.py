import random
import unittest

from flask import json

from pypot.creatures import PoppyErgoJr
from pypot.primitive.utils import Sinus

from utils import get_open_port


def jsonify(val):
    return json.loads(json.dumps(val))


class RestApiTestCase(unittest.TestCase):
    def setUp(self):
        self.jr = PoppyErgoJr(simulator='poppy-simu',
                              rest_api_port=get_open_port())
        self.app = self.jr.rest_api_server.app.test_client()

        for i in range(1, 4):
            s = Sinus(self.jr, 10.0, motor_list=self.jr.motors,
                      amp=random.random() * 10,
                      freq=random.random() * 0.1)

            self.jr.attach_primitive(s, 'sinus {}'.format(i))

    def assertIsClose(self, a, b, accuracy=1.0):
        if isinstance(b, float):
            if abs(float(a) - b) > accuracy:
                print(a, type(a), b, type(b), accuracy)

            self.assertTrue(abs(float(a) - b) < accuracy)
        else:
            if a != jsonify(b):
                print(a, type(a), b, type(b), accuracy)

            self.assertEqual(a, jsonify(b))

    def check_meta_and_get_data(self, rv):
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, 'application/json')

        return json.loads(rv.get_data())

    # [GET] /
    def test_heartbeat(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 204)

    # Devices
    # [GET] /devices?type=type
    def test_get_all_devices(self):
        rv = self.app.get('/devices')
        data = self.check_meta_and_get_data(rv)

        self.assertEqual({d['name'] for d in data['devices']},
                         {m.name for m in self.jr.motors + self.jr.sensors})

    def test_get_all_specific_devices(self):
        for device_type in ('motor', 'sensor'):
            rv = self.app.get('/devices?type={}'.format(device_type))
            data = self.check_meta_and_get_data(rv)

            types = {d['type'] for d in data['devices']}
            if types:
                self.assertEqual(types, {device_type})

            self.assertEqual({d['name'] for d in data['devices']},
                             {m.name for m in getattr(self.jr, '{}s'.format(device_type))})

    # [GET] /devices/device_name/registers
    def test_get_device_registers(self):
        devices = self.jr.motors + self.jr.sensors
        random.shuffle(devices)

        for dev in devices:
            rv = self.app.get('/devices/{}/registers'.format(dev.name))
            data = self.check_meta_and_get_data(rv)

            dev = getattr(self.jr, dev.name)

            self.assertEqual(set(data['registers'].keys()).union({'registers'}),
                             set(dev.registers))

            for reg, val in data['registers'].items():
                self.assertIsClose(val, getattr(dev, reg))

    # [GET] /devices/device_name/registers/register_name
    def test_get_device_specific_register(self):
        devices = self.jr.motors + self.jr.sensors
        random.shuffle(devices)

        for dev in devices:
            registers = list(dev.registers)
            random.shuffle(registers)

            for reg in registers:
                rv = self.app.get('/devices/{}/registers/{}'.format(dev.name, reg))
                data = self.check_meta_and_get_data(rv)

                self.assertEqual(data['register'],
                                 {
                                    'name': reg,
                                    'value': jsonify(getattr(dev, reg))
                                })

    # [PUT] /devices/device_name/registers/register_name
    # TODO

    # Groups
    # [GET] /groups
    def test_groups(self):
        rv = self.app.get('/groups')
        data = self.check_meta_and_get_data(rv)

        groups = {g['name'] for g in data['groups']}
        self.assertEqual(groups, set(self.jr.alias))

    # [GET]  /groups/group_name/registers?device_names=device_names&register_names=register_names
    def test_get_registers_of_whole_group(self):
        for group in self.jr.groups:
            rv = self.app.get('/groups/{}/registers'.format(group))
            data = self.check_meta_and_get_data(rv)

            devices = data['devices']
            self.assertEqual({m.name for m in getattr(self.jr, group)},
                             {d['name'] for d in devices})

            for d in devices:
                self.assertEqual(set(getattr(self.jr, d['name']).registers),
                                 set(d['registers'].keys()).union({'registers'}))

    def test_get_specific_reg_of_whole_group(self):
        for group in self.jr.groups:
            devices = getattr(self.jr, group)
            if not devices:
                continue
            device = random.choice(devices)
            registers = list(device.registers)
            random.shuffle(registers)

            for i in range(1, len(registers)):
                reg = registers[:i]
                reg_name = '&register_names='.join(reg)
                url = '/groups/{}/registers?register_names={}'.format(group, reg_name)

                rv = self.app.get(url)
                data = self.check_meta_and_get_data(rv)

                for d in data['devices']:
                    self.assertEqual(set(d['registers'].keys()), set(reg))

                    rd = getattr(self.jr, d['name'])
                    for r in reg:
                        self.assertIsClose(d['registers'][r], getattr(rd, r))

    def get_specific_reg_of_specific_devices(self):
        group = random.choice(self.jr.groups)

        devices = getattr(self.jr, group)
        if not devices:
            return

        random.shuffle(devices)
        devices = devices[:random.randint(1, len(devices))]

        registers = devices[0].registers
        random.shuffle(registers)
        registers = registers[:random.randint(1, 5)]# TODO: len(registers))]

        url = '/groups/{}/registers?device_names={}&register_names={}'.format(
            group,
            '&device_names='.join([d.name for d in devices]),
            '&register_names='.join(registers)
        )
        rv = self.app.get(url)
        data = self.check_meta_and_get_data(rv)

        self.assertEqual({d['name'] for d in data['devices']},
                         {d.name for d in devices})

        for d in data['devices']:
            self.assertEqual(set(d['registers'].keys()), set(registers))

            for r, v in d['registers'].items():
                self.assertEqual(v, jsonify(getattr(getattr(self.jr, d['name']), r)))

    def test_get_specific_reg_of_specific_devices(self):
        for _ in range(random.randint(1, 25)):
            self.get_specific_reg_of_specific_devices()

    # Primitives
    # [GET] /primitives?status=status
    def test_get_all_primitives(self):
        rv = self.app.get('/primitives')
        data = self.check_meta_and_get_data(rv)

        self.assertEqual({d['name'] for d in data['primitives']},
                         {p.name for p in self.jr.primitives})

    def test_get_all_specific_status_primitives(self):
        all_prim = []

        for status in ('running', 'paused', 'stopped'):
            rv = self.app.get('/primitives?status={}'.format(status))
            data = self.check_meta_and_get_data(rv)

            if data['primitives']:
                self.assertEqual({d['status'] for d in data['primitives']},
                                 {status})

                all_prim.extend([d['name'] for d in data['primitives']])

        self.assertEqual(len(all_prim), len(set(all_prim)))

        rv = self.app.get('/primitives')
        data = self.check_meta_and_get_data(rv)
        self.assertEqual(set(all_prim),
                         {d['name'] for d in data['primitives']})

    # [GET] /primitives/primitive_name
    def test_get_primitive(self):
        for p in self.jr.primitives:
            rv = self.app.get('/primitives/{}'.format(p.name))
            data = self.check_meta_and_get_data(rv)

            d = data['primitives']
            self.assertEqual(d['name'], p.name)
            self.assertEqual(d['status'], p.status)
            self.assertEqual(set([m['name'] for m in d['methods']]), set(p.methods))

            self.assertEqual(set(d['properties'].keys()), set(p.properties))
            for prop, val in d['properties'].items():
                self.assertIsClose(val, getattr(p, prop))

    # [GET] /primitives/primitive_name/properties/property_name
    def test_get_primitive_property(self):
        for p in self.jr.primitives:
            for prop in p.properties:
                rv = self.app.get('/primitives/{}/properties/{}'.format(p.name, prop))
                data = self.check_meta_and_get_data(rv)

                self.assertEqual(data['property']['name'], prop)
                self.assertIsClose(data['property']['value'], getattr(p, prop))

    # [PUT] /primitives/primitive_name/properties/property_name
    # TODO

    # [GET] /primitives/primitive_name/methods/method_name
    # TODO

    # TODO: functional testing
    # def test_led(self):
    #     c = random.choice(list(XL320LEDColors))
    #     m = random.choice(self.jr.motors)
    #
    #     r = self.get('/motor/{}/set/led/{}'.format(m.name, c.name))
    #     self.assertEqual(r.status_code, 200)
    #
    #     r = self.get('/motor/{}/get/led'.format(m.name))
    #     self.assertEqual(r.status_code, 200)
    #     self.assertEqual(r.text, c.name)

    def teardown(self):
        self.jr.close()


if __name__ == '__main__':
    unittest.main()

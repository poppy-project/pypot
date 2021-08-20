import unittest

import requests
import time
import json
from typing import Union

from pypot.creatures import PoppyErgoJr


class TestRestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jr = PoppyErgoJr(simulator='poppy-simu', use_http=True)
        cls.base_url = 'http://127.0.0.1:8080'
        cls.headers = {'Content-Type': 'application/json'}

        # Make sure the REST API is running before actually testing.
        while True:
            try:
                requests.get(cls.base_url + '/')
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)

    def get(self, url):
        url = '{}{}'.format(self.base_url, url)
        return requests.get(url)

    def post(self, url, data: Union[str, None] = None):
        url = '{}{}'.format(self.base_url, url)
        if data:
            return requests.post(url, data=data, headers=self.headers)
        return requests.post(url, headers=self.headers)

    def assert_status(self, answer, expected_code, request):
        self.assertEqual(expected_code, answer.status_code, "request " + request + " failed!")

    def one_line_assert(self, method, url, expected_code, data=None):
        """
        Makes a get/post request and also verifies the answer code.
        :param method: either self.get or self.post
        :param url: an url of the rest api
        :param expected_code: the code the request should give
        :param data: body request for post method (optional)
        :return: an assertion
        """
        if data:
            return self.assert_status(method(url, data), expected_code, method.__name__ + url)
        return self.assert_status(method(url), expected_code, method.__name__ + url)

    # region misc
    def test_ip(self):
        """ API REST test for request:
        GET /ip.json
        """
        url = '/ip.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, url)

    def test_index(self):
        """ API REST test for request:
        GET /robot.json
        """
        url = '/robot.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, url)

    def test_paths(self):
        """ API REST test for request:
        GET /
        """
        url = '/'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
    # endregion

    # region motors
    def test_motors_list(self):
        """ API REST test for request:
        GET /motors/list.json
        GET /motors/<alias>/list.json
        """
        url = '/motors/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
        response_json = json.loads(response.text)
        for m in ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']:  # Checks if all motors are present
            self.assertTrue(m in response_json["motors"], m + " could not be found in the list of motors")

        url = '/motors/motors/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

        url = '/motors/base/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
        response_json = json.loads(response.text)
        for m in ['m1', 'm2', 'm3']:  # Checks if all motors are present
            self.assertTrue(m in response_json["base"], m + " could not be found in the list of motors")

        url = '/motors/tip/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
        response_json = json.loads(response.text)
        for m in ['m4', 'm5', 'm6']:  # Checks if all motors are present
            self.assertTrue(m in response_json["tip"], m + " could not be found in the list of motors")

        url = '/motors/unknown_alias/list.json'  # Unknown alias
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_motors_aliases_list(self):
        """ API REST test for request:
        GET /motors/aliases/list.json
        """
        url = '/motors/aliases/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
        response_json = json.loads(response.text)
        for a in ['base', 'tip']:  # Checks if all aliases are present
            self.assertTrue(a in response_json["aliases"], a + " could not be found in the list of aliases")

    def test_motors_registers_list(self):
        """ API REST test for request:
        GET /motors/<motor_name>/registers/list.json
        """
        url = '/motors/m1/registers/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
        response_json = json.loads(response.text)
        for r in ['goal_speed', 'compliant', 'safe_compliant', 'angle_limit', 'id', 'name', 'model', 'present_position',
                  'goal_position', 'present_speed', 'moving_speed', 'present_load', 'torque_limit', 'lower_limit',
                  'upper_limit', 'present_voltage', 'present_temperature', 'pid', 'led', 'control_mode']:
            self.assertTrue(r in response_json["registers"], r + " could not be found in the list of registers")

        url = '/motors/unknown_motor/registers/list.json'  # Unknown motor
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_motor_register(self):
        """ API REST test for request:
        GET /motors/<motor_name>/registers/<register_name>/value.json
        POST /motors/<motor_name>/registers/<register_name>/value.json + new_value
        """
        url = '/motors/m1/registers/present_position/value.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

        url = '/motors/unknown_motor/registers/present_position/value.json'  # Unknown motor
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

        url = '/motors/m1/registers/unknown_register/value.json'  # Unknown register
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

        url = '/motors/m1/registers/compliant/value.json'  # OK
        data = 'true'
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/motors/unknown_motor/registers/compliant/value.json'  # Unknown motor
        data = 'true'
        response = self.post(url, data)
        self.assert_status(response, 404, 'POST ' + url)

        url = '/motors/m1/registers/unknown_register/value.json'  # Unknown register
        data = 'true'
        response = self.post(url, data)
        self.assert_status(response, 404, 'POST ' + url)

        url = '/motors/m1/registers/compliant/value.json'  # Wrong value
        data = 'wrong_value'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

    def test_motor_register_values(self):
        """ API REST test for request:
        GET /motors/registers/<register_name>/list.json
        """
        url = '/motors/registers/compliant/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)
        response_json = json.loads(response.text)
        for m in ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']:
            self.assertTrue(m in response_json["compliant"], m + " could not be found in the list of motors")

        url = '/motors/registers/unknown_register/list.json'  # Unknown register
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)
    # endregion

    # region goto
    def test_motor_goto(self):
        """ API REST test for request:
        POST /motors/<motor_name>/goto.json + position & duration & wait
        """
        url = '/motors/m1/goto.json'  # OK
        data = '{"position":10,"duration":"3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/motors/m1/goto.json'  # Wrong duration
        data = '{"position":10,"duration":"-3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

        url = '/motors/m1/goto.json'  # At least one value is missing
        data = '{"duration":"3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

    def test_motors_goto(self):
        """ API REST test for request:
        POST /motors/goto.json + motors & their positions & duration & wait
        """
        url = '/motors/goto.json'  # OK
        data = '{"motors":["m1", "m2"], "positions":[0,10],"duration":"3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/motors/goto.json'  # Different amount of motors and positions
        data = '{"motors":["m1"], "positions":[0,10],"duration":"3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

        url = '/motors/goto.json'  # Wrong duration
        data = '{"motors":["m1", "m2"], "positions":[0,10],"duration":"-3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

        url = '/motors/goto.json'  # At least one value is missing
        data = '{"positions":[0,10],"duration":"3","wait":"true"}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)
    # endregion

    # region sensors
    def test_sensors_list(self):
        """ API REST test for request:
        GET /sensors/list.json
        """
        url = '/sensors/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

    def test_sensor_registers_list(self):
        """ API REST test for request:
        GET /sensors/<sensor_name>/registers/list.json
        """
        # There is no sensor on a poppy-simu robot
        # url = '/sensors/camera/registers/list.json'  # OK
        # response = self.get(url)
        # self.assert_status(response, 200, 'GET ' + url)

        url = '/sensors/unknown_sensor/registers/list.json'  # Unknown sensor
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_sensor_register(self):
        """ API REST test for request:
        GET /sensors/<sensor_name>/registers/<register_name>/value.json
        POST /sensors/<sensor_name>/registers/<register_name>/value.json + new_value
        """
        # There is no sensor on a poppy-simu robot
        # url = '/sensors/camera/registers/resolution/value.json'  # OK
        # response = self.get(url)
        # self.assert_status(response, 200, 'GET ' + url)

        url = '/sensors/unknown_sensor/registers/unknown_register/value.json'  # Unknown sensor or register
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

        url = '/sensors/unknown_sensor/registers/unknown_register/value.json'  # Unknown sensor or register
        data = 'wrong_value'
        response = self.post(url, data)
        self.assert_status(response, 404, 'POST ' + url)
    # endregion

    # region records
    def test_records_list(self):
        """ API REST test for request:
        GET /records/list.json
        """
        url = '/records/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

    def test_records_values(self):
        """ API REST test for request:
        GET records/<move_name>/value.json
        """
        self.one_line_assert(self.post, '/records/unit_test/record.json', 202)  # Creates a record 'unit_test'
        self.one_line_assert(self.post, '/records/unit_test/save.json', 202)

        url = '/records/unit_test/value.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

        url = '/records/unit_test2/value.json'  # Unknown move name
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

        self.one_line_assert(self.post, '/records/unit_test/delete.json', 202)   # Deletes the record 'unit_test'

    def test_records_record_and_save(self):
        """ API REST test for request:
        POST /records/<move_name>/record.json [+ motors] (optional)
        """
        url = '/records/unit_test/record.json'  # OK
        data = None
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/records/unit_test/save.json'  # OK
        data = '{}'
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        response = json.loads(self.get('/records/list.json').text)  # Checks if move has been created
        self.assertTrue('unit_test' in response["moves"], "Move unit_test was not created")

        url = '/records/unit_test/record.json'  # OK
        data = '{"motors":["m1","m2"]}'
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/records/unit_test/save.json'  # OK
        data = None
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/records/unit_test2/save.json'  # Unknown move name
        data = None
        response = self.post(url, data)
        self.assert_status(response, 404, 'POST ' + url)

        self.one_line_assert(self.post, '/records/unit_test/delete.json', 202)   # Deletes the record 'unit_test'

    def test_record_delete(self):
        """ API REST test for request:
        POST records/<move_name>/delete.json
        """
        self.one_line_assert(self.post, '/records/unit_test/record.json', 202)  # Creates a record 'unit_test'
        self.one_line_assert(self.post, '/records/unit_test/save.json', 202)

        url = '/records/unit_test/delete.json'  # OK
        data = None
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

    def test_record_play(self):
        """ API REST test for request:
        POST /records/<move_name>/play.json + speed
        """
        self.one_line_assert(self.post, '/records/unit_test/record.json', 202)  # Creates a record 'unit_test'
        self.one_line_assert(self.post, '/records/unit_test/save.json', 202)

        url = '/records/unit_test/play.json'  # OK
        data = '{"speed": -1}'
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        self.one_line_assert(self.post, '/records/unit_test/stop.json', 202)  # Stops the replay

        url = '/records/unit_test/play.json'  # No speed field
        data = '{"sped": -1}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

        url = '/records/unit_test/play.json'  # Unknown speed
        data = '{"speed": unreadable_speed}'
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

        url = '/records/unit_test2/play.json'  # Unknown move name
        data = '{"speed": -1}'
        response = self.post(url, data)
        self.assert_status(response, 404, 'POST ' + url)

        self.one_line_assert(self.post, '/records/unit_test/delete.json', 202)   # Deletes the record 'unit_test'

    def test_record_stop(self):
        """ API REST test for request:
        POST /records/<move_name>/stop.json
        """
        self.one_line_assert(self.post, '/records/unit_test/record.json', 202)  # Creates a record 'unit_test'
        self.one_line_assert(self.post, '/records/unit_test/save.json', 202)
        self.one_line_assert(self.post, '/records/unit_test/play.json', 202, '{"speed": 1}')  # Starts a move replay

        url = '/records/unit_test/stop.json'  # OK
        data = None
        response = self.post(url, data)
        self.assert_status(response, 202, 'POST ' + url)

        url = '/records/unit_test2/stop.json'  # Unknown move name
        data = None
        response = self.post(url, data)
        self.assert_status(response, 400, 'POST ' + url)

        self.one_line_assert(self.post, '/records/unit_test/delete.json', 202)   # Deletes the record 'unit_test'
    # endregion

    # region primitives
    def test_primitives_list(self):
        """ API REST test for request:
        GET /primitives/list.json
        """
        url = '/primitives/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

    def test_running_primitives_list(self):
        """ API REST test for request:
        GET /primitives/running/list.json
        """
        url = '/primitives/running/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

    def test_start_primitive(self):
        """ API REST test for request:
        GET /primitives/<primitive_name>/start.json
        """
        url = '/primitives/base_posture/start.json'  # OK
        response = self.get(url)
        self.assert_status(response, 202, 'GET ' + url)

        url = '/primitives/unknown_primitive/start.json'  # Unknown primitive
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_stop_primitive(self):
        """ API REST test for request:
        GET /primitives/<primitive_name>/stop.json
        """
        self.one_line_assert(self.get, '/primitives/base_posture/start.json', 202)  # Starts a primitive

        url = '/primitives/base_posture/stop.json'  # OK
        response = self.get(url)
        self.assert_status(response, 202, 'GET ' + url)

        url = '/primitives/unknown_primitive/stop.json'  # Unknown primitive
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_pause_primitive(self):
        """ API REST test for request:
        GET /primitives/<primitive_name>/pause.json
        """
        self.one_line_assert(self.get, '/primitives/base_posture/start.json', 202)  # Starts a primitive

        url = '/primitives/base_posture/pause.json'  # OK
        response = self.get(url)
        self.assert_status(response, 202, 'GET ' + url)

        url = '/primitives/unknown_primitive/pause.json'  # Unknown primitive
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_resume_primitive(self):
        """ API REST test for request:
        GET /primitives/<primitive_name>/resume.json
        """
        self.one_line_assert(self.get, '/primitives/base_posture/start.json', 202)  # Starts a primitive
        self.one_line_assert(self.get, '/primitives/base_posture/pause.json', 202)  # Pauses the primitive

        url = '/primitives/base_posture/resume.json'  # OK
        response = self.get(url)
        self.assert_status(response, 202, 'GET ' + url)

        url = '/primitives/unknown_primitive/resume.json'  # Unknown primitive
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_primitive_properties_list(self):
        """ API REST test for request:
        GET /primitives/<primitive_name>/properties/list.json
        """
        url = '/primitives/base_posture/properties/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

        url = '/primitives/unknown_primitive/properties/list.json'  # Unknown primitive
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)

    def test_primitive_methods_list(self):
        """ API REST test for request:
        GET /primitives/<primitive_name>/methods/list.json
        """
        url = '/primitives/base_posture/methods/list.json'  # OK
        response = self.get(url)
        self.assert_status(response, 200, 'GET ' + url)

        url = '/primitives/unknown_primitive/methods/list.json'  # Unknown primitive
        response = self.get(url)
        self.assert_status(response, 404, 'GET ' + url)
    # endregion


if __name__ == '__main__':
    unittest.main()

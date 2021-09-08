import json
import socket
import errno
import numpy
import logging

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler
from tornado.web import Application

from .server import AbstractServer

logger = logging.getLogger(__name__)


class MyJSONEncoder(json.JSONEncoder):
	""" JSONEncoder which tries to call a json property before using the encoding default function. """

	def default(self, obj):
		if hasattr(obj, 'json'):
			return obj.json

		if isinstance(obj, numpy.ndarray):
			return list(obj)

		if isinstance(obj, numpy.integer):
			return int(obj)

		return json.JSONEncoder.default(self, obj)


class PoppyRequestHandler(RequestHandler):
	"""Custom request handler.

	Automatically sets CORS and cache headers, and manages
	every OPTIONS request."""

	def set_default_headers(self):
		self.set_header('Cache-control', 'no-store')
		self.set_header('Access-Control-Allow-Origin', '*')
		self.set_header('Access-Control-Allow-Headers', 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token')
		self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')

	def options(self, *args, **kwargs):
		self.set_status(204)

	def write_json(self, obj):
		self.write(json.dumps(obj, cls=MyJSONEncoder))


# region Miscellaneous Handlers

class LocalIp(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /ip.json
	"""

	def get(self):
		import socket

		def find_local_ip():
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			local_ip = s.getsockname()[0]
			s.close()
			return local_ip

		try:
			ip = find_local_ip()
			self.set_status(200)
			self.write_json({
				"ip": ip
			})
		except socket.error as e:
			self.set_status(404)
			self.write_json({
				"error": "Cannot find ip of your Poppy Robot",
				"tip": "Poppy is unable to resolve its ip. Try to resolve it using ifconfig / ipconfig.",
				"details": "{}".format(" ".join(str(e.args)))
			})


class IndexHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /robot.json
	"""
	def get(self):
		out = {
			'motors': [],
			'primitives': []
		}
		for m in self.restful_robot.get_motors_list('motors'):
			motor = {}
			for r in self.restful_robot.get_motor_registers_list(m):
				try:
					motor[r] = self.restful_robot.get_motor_register_value(m, r)
				except AttributeError:
					pass
			out['motors'].append(motor)

		running_primitives = self.restful_robot.get_running_primitives_list()
		for prim in self.restful_robot.get_primitives_list():
			primitive = {
				'primitive': prim,
				'running': prim in running_primitives,
				'properties': [],
				# XXX pas de self en param ?
				'methods': self.restful_robot.get_primitive_methods_list(prim)
			}
			for prop in self.restful_robot.get_primitive_properties_list(prim):
				primitive['properties'].append({
					'property': prop,
					'value': self.restful_robot.get_primitive_property(prim, prop)
				})
			out['primitives'].append(primitive)
		self.set_status(200)
		self.write_json(out)


class PathsUrl(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /
	"""
	@staticmethod
	def has_method(class_obj, method_name):
		return method_name in class_obj.__dict__

	def get(self):
		out = '<b>All url paths available:</b><br>'
		get = '<br><b>Get method url:</b><br>'
		post = '<br><b>Post method url:</b><br>'
		for url in url_paths:
			tmp = url[0]
			tmp = tmp.replace('\\', '')
			tmp = tmp.replace('?', '')
			tmp = tmp.replace('<', '&lt')
			tmp = tmp.replace('>', '&gt')
			tmp = tmp.replace('(P', '')
			tmp = tmp.replace('[a-zA-Z0-9_]+)', '')
			if self.has_method(url[1], 'get'):
				get += tmp + '<br>'
			if self.has_method(url[1], 'post'):
				post += tmp + '<br>'
		out += get
		out += post
		self.set_status(200)
		self.write(out)


# endregion

# region Motors Handlers

class MotorsListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /motors/list.json
	GET /motors/<alias>/list.json
	"""

	def get(self, alias='motors'):
		try:
			motors = self.restful_robot.get_motors_list(alias)
			self.set_status(200)
			self.write_json({
				alias: motors
			})
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "Alias '{}' does not exist.".format(alias),
				"tip": "You can find the list of aliases with /motors/aliases/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class MotorsAliasesListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /motors/aliases/list.json
	"""

	def get(self):
		aliases = self.restful_robot.get_motors_alias()
		self.set_status(200)
		self.write_json({
			"aliases": aliases
		})


class MotorRegistersListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /motors/<motor_name>/registers/list.json
	"""

	def get(self, motor_name):
		try:
			self.set_status(200)
			self.write_json({
				'registers': self.restful_robot.get_motor_registers_list(motor_name)
			})
		except AttributeError as e:
			# required motor does not exist
			self.set_status(404)
			self.write_json({
				"error": "Motor '{}' does not exist.".format(motor_name),
				"tip": "You can find the list of motors with /motors/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class MotorRegisterHandler(PoppyRequestHandler):
	""" API REST Request Handler for requests:
	GET /motors/<motor_name>/registers/<register_name>/value.json
	POST /motors/<motor_name>/registers/<register_name>/value.json + new_value
	"""

	def get(self, motor_name, register_name):
		try:
			self.set_status(200)
			self.write_json({
				register_name: self.restful_robot.get_motor_register_value(motor_name, register_name)
			})
		except AttributeError as e:
			# either motor given does not exist or the motor does not have the required register.
			self.set_status(404)
			self.write_json({
				"error": "Either motor '{}' or register '{}' does not exist. Or you want to change a read-only register"
						 " value".format(motor_name, register_name),
				"tip": "You can find the list of motors with /motors/list.json and their registers with "
					   "/motors/<motor_name>/registers/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})

	def post(self, motor_name, register_name):
		try:
			data = json.loads(self.request.body.decode())
		except json.decoder.JSONDecodeError as jsDE:
			self.set_status(400)
			self.write_json({
				"error": "Data given is not valid.",
				"tip": "{}".format(" ".join(jsDE.args))
			})
			return  # we have to stop the function if data isn't well defined
		try:
			self.restful_robot.set_motor_register_value(motor_name, register_name, data)
			self.set_status(202)
			self.write_json({
				register_name: data
			})
		except AttributeError as e:
			# either motor given does not exist or the motor does not have the required register.
			self.set_status(404)
			self.write_json({
				"error": "Either motor '{}' or register '{}' does not exist.".format(motor_name, register_name),
				"tip": "You can find the list of motors with /motors/list.json and their registers with "
					   "/motors/<motor_name>/registers/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class RegisterValuesHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /motors/registers/<register_name>/list.json
	"""

	def get(self, register_name):
		try:
			register_values = {}
			for m in self.restful_robot.get_motors_list('motors'):
				value = self.restful_robot.get_motor_register_value(m, register_name)
				register_values[m] = value
			self.set_status(200)
			self.write_json({
				register_name: register_values
			})
		except AttributeError as e:
			# motor does not have the required register.
			self.set_status(404)
			self.write_json({
				"error": "A motor does not have the register '{}'.".format(register_name),
				"tip": "You can find the list of the registers of a motor with /motors/<motor_name>/registers/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


# endregion

# region Goto Handlers

class MotorsGotoHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /motors/goto.json + motors & their positions & duration & wait
	"""

	def post(self):
		try:
			data = json.loads(self.request.body.decode())
			motors = list(map(str, data["motors"]))  # motors field is a list
			positions = list(map(float, data["positions"]))  # positions field is a list
			duration = float(data["duration"])  # duration is a str or a float
			if duration <= 0:
				raise ValueError("Duration should be > 0")
			wait = bool(str(data["wait"]) in {'true', 'True', '1'})
			if len(motors) != len(positions):
				raise IndexError("There is not the same amount of motors and positions")
		except (ValueError, IndexError, AttributeError, KeyError) as e:
			self.set_status(400)
			self.write_json({
				"error": "Cannot read data given.",
				"tip": 'Four fields are required in this post request. "motors" is a list of motor names (given as '
					   'strings). "positions" is a list of angles for motors (given as strings or floats). '
					   '"duration" is the time in seconds to do the move, given as string or float."wait" is a boolean.'
					   ' Example: "{"motors": ["m1","m2"], "positions": [90, 0]}',
				"details": "{}".format(" ".join(str(e.args)))
			})
			return  # we have to stop the function if data isn't well defined
		try:
			self.restful_robot.set_goto_positions_for_motors(motors, positions, duration, wait=wait)
			self.set_status(202)
			motor_positions = {}
			for m, motors in enumerate(motors):
				motor_positions[motors] = positions[m]
			self.write_json({
				"motors": motor_positions,
				"duration": duration,
				"waiting": wait
			})
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "One of the motors given does not exist.",
				"tip": "You can find the list of motors with /motors/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class MotorGotoHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /motors/<motor_name>/goto.json + position & duration & wait
	"""

	def post(self, motor_name):
		try:
			data = json.loads(self.request.body.decode())
			position = float(data["position"])
			duration = float(data["duration"])
			if duration <= 0:
				raise ValueError("Duration should be > 0")
			wait = bool(str(data["wait"]) in {'true', 'True', '1'})
		except (ValueError, AttributeError, KeyError) as e:
			self.set_status(400)
			self.write_json({
				"error": "Cannot read data given.",
				"tip": 'Three fields are required in this post request. "position" a angle for the motor, given as '
					   'string or float. "duration" is the time in seconds to do the move, given as string or float.'
					   '"wait" is a boolean. Example: "{"motor": "m1", "position": 90, duration: 3, wait: "true"}',
				"details": "{}: {}".format(type(e).__name__, " ".join(e.args))
			})
			return  # we have to stop the function if data isn't well defined
		try:
			self.restful_robot.set_goto_position_for_motor(motor_name, position, duration, wait=wait)
			self.set_status(202)
			self.write_json({
				"motors": {
					motor_name: position
				},
				"duration": duration,
				"waiting": wait
			})
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "Motor '{}' does not exist.".format(motor_name),
				"tip": "You can find the list of motors with /motors/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


# endregion

# region Sensors Handlers

class SensorsListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /sensors/list.json
	"""

	def get(self):
		self.write_json({
			"sensors": self.restful_robot.get_sensors_list()
		})


class SensorRegistersListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /sensors/<sensor_name>/registers/list.json
	"""

	def get(self, sensor_name):
		try:
			self.set_status(200)
			self.write_json({
				'registers': self.restful_robot.get_sensors_registers_list(sensor_name)
			})
		except AttributeError as e:
			# required sensor does not exist
			self.set_status(404)
			self.write_json({
				"error": "Sensor '{}' does not exist.".format(sensor_name),
				"tip": "You can find the list of sensors with /sensors/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class SensorRegisterHandler(PoppyRequestHandler):
	""" API REST Request Handler for requests:
	GET /sensors/<sensor_name>/registers/<register_name>/value.json
	POST /sensors/<sensor_name>/registers/<register_name>/value.json + new_value
	"""

	def get(self, sensor_name, register_name):
		try:
			self.set_status(200)
			self.write_json({
				register_name: self.restful_robot.get_sensor_register_value(sensor_name, register_name)
			})
		except AttributeError as e:
			# either sensor given does not exist or the sensor does not have the required register.
			self.set_status(404)
			self.write_json({
				"error": "Either sensor '{}' or register '{}' does not exist.".format(sensor_name, register_name),
				"tip": "You can find the list of sensors with /sensors/list.json and their registers with "
					   "/sensors/<sensor_name>/registers/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})

	def post(self, sensor_name, register_name):
		try:
			data = json.loads(self.request.body.decode())
		except json.decoder.JSONDecodeError as jsDE:
			self.set_status(404)
			self.write_json({
				"error": "Data given is not valid.",
				"tip": "{}".format(" ".join(jsDE.args))
			})
			return  # we have to stop the function if data isn't well defined
		try:
			self.restful_robot.set_sensor_register_value(sensor_name, register_name, data)
			self.set_status(202)
			self.write_json({
				register_name: data
			})
		except AttributeError as e:
			# either sensor given does not exist or the sensor does not have the required register.
			self.set_status(404)
			self.write_json({
				"error": "Either sensor '{}' or register '{}' does not exist. Or you want to change a read-only register"
						 " value".format(sensor_name, register_name),
				"tip": "You can find the list of sensors with /sensors/list.json and their registers with "
					   "/sensors/<sensor_name>/registers/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class CameraHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /sensors/camera/frame.png
	"""

	def get(self):
		try:
			frame = self.restful_robot.getFrameFromCamera()
			self.set_status(200)
			self.set_header('Content-type', 'image/png')
			self.write(frame)
		except AttributeError as e:
			# Camera is not available.
			self.set_status(404)
			self.write_json({
				"error": "No camera was found.",
				"tip": "Verify your camera is well plugged. On http://poppy.local/logs, verify camera is enabled. If "
				       "you are simulating a Poppy robot, you will unfortunately not be able to use the camera",
				"details": "{}".format(" ".join(str(e.args)))
			})

class MarkerDetectorHandler(PoppyRequestHandler):
	""" API REST Request Handler for requests:
	GET /sensors/code/list.json
	GET /sensors/code/<code_name>.json
	"""

	def get(self, code_name):
		self.set_status(200)
		if code_name == 'list':
			self.write_json({
				"codes": self.restful_robot.markers_list()
			})
		else:
			try:
				self.set_status(200)
				self.write_json({
					"found": self.restful_robot.detect_marker(code_name)
				})
			except AttributeError as e:
				# QRcode is not implemented
				self.set_status(404)
				self.write_json({
					"error": "Code detection has been removed from robot",
					"tip": "Add marker_detector in software/poppy_ergo_jr/configuration/poppy_ergo_jr.json",
					"details": "{}".format(" ".join(str(e.args)))
				})
			except KeyError as e:
				# Code asked is not defined
				self.set_status(404)
				self.write_json({
					"error": "The code you asked for does not exist",
					"tip": "All preset codes are caribou, tetris and lapin/rabbit",
					"details": "{}".format(" ".join(str(e.args)))
				})

# endregion

# region Moves Handlers

class ListRecordedMovesHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /records/list.json
	"""

	def get(self):
		self.set_status(200)
		self.write_json({
			"moves": self.restful_robot.get_available_record_list()
		})


class RecordMoveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /records/<move_name>/record.json [+ motors] (optional)
	"""

	def post(self, move_name):
		try:
			data = json.loads(self.request.body.decode())
			motors = data["motors"]
		except json.decoder.JSONDecodeError:  # body is empty
			motors = self.restful_robot.get_motors_list('motors')
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "Cannot read data given.",
				"tip": "Motors should be given with json format either as a string, with motor names separated by a "
					   "comma (,), or as a list. Example: {'motors': 'm1,m2'} or {'motors': ['m1', 'm2']} ",
				"details": "{}".format(" ".join(str(e.args)))
			})
			return  # we have to stop the function if data isn't well defined
		if motors:
			# Recording only the moves of the motors given
			try:
				# transforms a string separated by semi-colons to a list
				if isinstance(motors, str):
					motors = motors.split(',')
				self.restful_robot.start_move_recorder(move_name, motors)
			except AttributeError as e:
				self.set_status(404)
				self.write_json({
					"error": "At least one of the motors given could not be found.",
					"tip": "Motors should be given with json format either as a string, with motor names separated by "
						   'a comma (,), or as a list. Example: {"motors": "m1,m2"} or {"motors": ["m1", "m2"]}',
					"details": "{}".format(" ".join(str(e.args)))
				})
				return  # we have to stop the function if data isn't well defined
		else:
			self.restful_robot.start_move_recorder(move_name)
		self.set_status(202)
		self.write_json({
			move_name: "recording"
		})


class SaveMoveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /records/<move_name>/save.json
	"""

	def post(self, move_name):
		# No data is required
		try:
			self.restful_robot.stop_move_recorder(move_name)
			self.set_status(202)
			self.write_json({
				move_name: "saved"
			})
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "The move you want to save is not being recorded.",
				"tip": "Start by recording a move with /records/<move_name>/record.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class MoveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET records/<move_name>/value.json
	"""

	def get(self, move_name):
		try:
			self.set_status(200)
			info = self.restful_robot.get_move_recorder(move_name)
			self.write_json({
				move_name: info,
				"length": len(info)
			})
		except FileNotFoundError as e:
			self.set_status(404)
			self.write_json({
				"error": "The move you want to play does not exist.",
				"tip": "Start by recording a move with /records/<move_name>/record.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class PlayMoveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /records/<move_name>/play.json + speed
	"""

	def post(self, move_name):
		try:
			data = json.loads(self.request.body.decode())
			speed = data["speed"]
			speed = float(speed)
			opposite_direction = False  # play move forward by default

			if speed < 0:
				# if speed is negative, then play move backwards
				opposite_direction = True
				speed = abs(speed)
		except (KeyError, json.decoder.JSONDecodeError) as jde:  # speed field is missing
			self.set_status(400)
			self.write_json({
				"error": "speed field is missing.",
				"tip": 'Speed value should be given with json format as a string, and with a minus sign (-) if you '
					   'want to play the move backwards. Example: {"speed": "-1.0"}',
				"details": "{}".format(" ".join(jde.args))
			})
			return  # we have to stop the function if data isn't well defined
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "Cannot read data given.",
				"tip": 'Speed value should be given with json format as a string, and with a minus sign (-) if you '
					   'want to play the move backwards. Example: {"speed": "-1.0"}',
				"details": "{}".format(" ".join(str(e.args)))
			})
			return  # we have to stop the function if data isn't well defined

		try:
			self.restful_robot.start_move_player(move_name, speed=speed, backwards=opposite_direction)
			self.set_status(202)
			self.write_json({
				move_name: "started replay"
			})
		except FileNotFoundError as e:
			self.set_status(404)
			self.write_json({
				"error": "The move you want to play does not exist.",
				"tip": "Start by recording a move with /records/<move_name>/record.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class StopMoveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /records/<move_name>/stop.json
	"""

	def post(self, move_name):
		try:
			# No data is required
			self.restful_robot.stop_primitive('_{}_player'.format(move_name))
			self.set_status(202)
			self.write_json({
				move_name: "stopped"
			})
		except AttributeError as e:
			self.set_status(400)
			self.write_json({
				"error": "The move you want to stop has not started.",
				"tip": "Start by playing a move with /records/<move_name>/play.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class DeleteMoveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /records/<move_name>/delete.json
	"""

	def post(self, move_name):
		# No data is required
		success = self.restful_robot.remove_move_record(move_name)
		if success:
			self.set_status(202)
			self.write_json({
				move_name: "deleted"
			})
		else:
			self.set_status(404)
			self.write_json({
				"error": "The move you want to delete does not exist.",
				"tip": "Start by recording a move with /records/<move_name>/record.json",
				"details": "No file {}.record was found".format(move_name)
			})


# endregion

# region Primitives Handlers

class PrimitivesListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/list.json
	"""

	def get(self):
		self.set_status(200)
		self.write_json({
			"primitives": self.restful_robot.get_primitives_list()
		})


class RunningPrimitivesListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/running/list.json
	"""

	def get(self):
		self.set_status(200)
		self.write_json({
			"running_primitives": self.restful_robot.get_running_primitives_list()
		})


class StartPrimitiveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/<primitive_name>/start.json
	"""

	def get(self, primitive_name):
		try:
			self.restful_robot.start_primitive(primitive_name)
			self.set_status(202)
			self.write_json({
				primitive_name: "started"
			})
		except AttributeError as e:
			# Primitive does not exist
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class StopPrimitiveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/<primitive_name>/stop.json
	"""

	def get(self, primitive_name):
		try:
			self.restful_robot.stop_primitive(primitive_name)
			self.set_status(202)
			self.write_json({
				primitive_name: "stopped"
			})
		except AttributeError as e:
			# Primitive does not exist
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class PausePrimitiveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/<primitive_name>/pause.json
	"""

	def get(self, primitive_name):
		try:
			self.restful_robot.pause_primitive(primitive_name)
			self.set_status(202)
			self.write_json({
				primitive_name: 'paused'
			})
		except AttributeError as e:
			# Primitive does not exist
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class ResumePrimitiveHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/<primitive_name>/resume.json
	"""

	def get(self, primitive_name):
		try:
			self.restful_robot.resume_primitive(primitive_name)
			self.set_status(202)
			self.write_json({
				primitive_name: 'resumed'
			})
		except AttributeError as e:
			# Primitive does not exist
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class PrimitivePropertiesListHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/<primitive_name>/properties/list.json
	"""

	def get(self, primitive_name):
		try:
			self.set_status(200)
			self.write_json({
				'property': self.restful_robot.get_primitive_properties_list(primitive_name)
			})
		except AttributeError as e:
			# Primitive does not exist
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class PrimitivePropertyHandler(PoppyRequestHandler):
	def get(self, primitive_name, prop):
		response = self.restful_robot.get_primitive_property(primitive_name, prop)
		self.write_json({
			'{}.{}'.format(primitive_name, prop): response
		})

	def post(self, primitive_name, prop):
		data = json.loads(self.request.body.decode())
		self.restful_robot.set_primitive_property(primitive_name, prop, data)
		self.set_status(204)


class ListPrimitiveMethodsHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /primitives/<primitive_name>/methods/list.json
	"""

	def get(self, primitive_name):
		try:
			self.set_status(200)
			self.write_json({
				'methods': self.restful_robot.get_primitive_methods_list(primitive_name)
			})
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


class CallPrimitiveMethodHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	POST /primitives/<primitive_name>/methods/<method_name>/args.json
	"""

	def post(self, primitive_name, method_name):
		try:
			data = json.loads(self.request.body.decode())
			response = self.restful_robot.call_primitive_method(primitive_name, method_name, data)
			self.write_json({
				'{}:{}'.format(primitive_name, method_name): response
			})
		except AttributeError as e:
			self.set_status(404)
			self.write_json({
				"error": "Primitive '{}' does not exist".format(primitive_name),
				"tip": "You can find the list of the primitives with /primitives/list.json",
				"details": "{}".format(" ".join(str(e.args)))
			})


# endregion

# region IK Handlers

# Chain name(s) for
#     * Ergo Jr is 'chain' (https://github.com/poppy-project/poppy-ergo-jr/blob/47dd208ab256a526fbd89653b3f4f996ca503a65/software/poppy_ergo_jr/poppy_ergo_jr.py#L27)
#     * Torso are 'l_arm_chain' and 'r_arm_chain' (https://github.com/poppy-project/poppy-torso/blob/f1de072c88e7d6e0702664aec5028fb8266d37a4/software/poppy_torso/poppy_torso.py#L39)
#     * Humanoid do not have IK chains yet.

class IKValueHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /ik/<chain_name>/value.json
	It returns the xyz coordinates of the effector and the list [Rx.x, Rx.y, Rx.z], which is the transformation along X
	axis. Those values may not readable by a humain. The goal is to replace 'rot' values by roll, pitch and yaw.
	"""

	def get(self, chain_name):
		try:
			self.set_status(200)
			ans = self.restful_robot.ik_endeffector(chain_name)
			# Prints a curl command which instructs the robot to reach the current position.
			# command = "curl -X POST \\\n\t-H 'Content-Type: application/json' \\\n\t-d '{\"xyz\": \"" + ans[0] +\
			#          "\", \"xyz\": \"" + ans[1] + "\", \"duration\":\"3\", \"wait\":\"True\"}'" \
			#                                       "\\\n\thttp://localhost\\:8080/ik/chain/goto.json "
			# print(command)
			self.write_json({
				"xyz": ans[0],
				"rot": ans[1],
			})
		except AttributeError as e:
			# chain given does not exist.
			self.set_status(404)
			self.write_json({
				"error": "Chain '{}' does not exist for this robot".format(chain_name),
				"tip": "The Ergo's Chain names are 'chain', the Torso's are 'l_arm_chain' and 'l_arm_chain' and the"
					   " Humanoid has none.",
				"details": "{}".format(" ".join(str(e.args)))
			})
		except Exception as ex:
			template = "An exception of type {0} occured. Arguments:\n{1}"
			message = template.format(type(ex).__name__, " ".join(ex.args))
			self.set_status(400)
			self.write_json({"error": message})


class IKGotoHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /ik/<chain_name>/goto.json + duration, [x,y,z], [, wait][, rotation]
	IK is not operational. You may encounter difficulties while requesting an orientation AND a position.
	Orientation will take priority over position.
	"""

	def post(self, chain_name):
		try:
			data = json.loads(self.request.body.decode())
			duration = float(data["duration"])  # in seconds
			wait = data["wait"] if "wait" in data else False  # wait is set to False if not defined

			# position: list [x, y, z]
			xyz = list(map(float, str(data["xyz"]).split(","))) if "xyz" in data else None

			# rotation: list [TransformXAxis.x, TransformXAxis.y, TransformXAxis.z]
			rot = list(map(float, str(data["rot"]).split(","))) if "rot" in data else None

			# roll/pitch/yaw: list [roll, pitch, yaw]
			rpy = list(map(float, str(data["rpy"]).split(","))) if "rpy" in data else None
			if rpy:
				# When rpy is defined, it overwrites the value of rotation
				# The function ik_rpy converts a list of rpy into a 3x3 rotation matrix
				rot = self.restful_robot.ik_rpy(chain_name, *rpy)

			print("/!\\ IK Post method has some problems with orientation. It will prioritize orientation over position.")
			# goto requested position. Returned value is the real position (cartesian + rotation) of the end effector
			pose = self.restful_robot.ik_goto(chain_name, xyz, rot, duration, wait)

			self.set_status(200)
			self.write_json({
				"xyz": pose[0],
				"rot": pose[1]
			})
		except AttributeError as e:
			# chain given does not exist.
			self.set_status(404)
			self.write_json({
				"error": "Chain '{}' does not exist for this robot".format(chain_name),
				"tip": "The Ergo's Chain names are 'chain', the Torso's are 'l_arm_chain' and 'l_arm_chain' and the"
					   " Humanoid has none.",
				"details": "{}".format(" ".join(str(e.args)))
			})
		except Exception as ex:
			template = "An exception of type {0} occured. Arguments:\n{1}"
			message = template.format(type(ex).__name__, " ".join(ex.args))
			self.set_status(400)
			self.write_json({"error": message})


class IKRPYHandler(PoppyRequestHandler):
	""" API REST Request Handler for request:
	GET /ik/<chain_name>/rpy.json + r, p, y
	It is mainly used for debug, it may be removed when IK is operationnal
	"""

	def get(self, chain_name):
		try:
			data = json.loads(self.request.body.decode())
			r = float(data["r"])
			p = float(data["p"])
			y = float(data["y"])
			self.set_status(200)
			self.write_json({
				"rpy": self.restful_robot.ik_rpy(chain_name, r, p, y)
			})
		except AttributeError as e:
			# chain given does not exist.
			self.set_status(404)
			self.write_json({
				"error": "Chain '{}' does not exist for this robot".format(chain_name),
				"tip": "The Ergo's Chain names are 'chain', the Torso's are 'l_arm_chain' and 'l_arm_chain' and the"
					   " Humanoid has none.",
				"details": "{}".format(" ".join(str(e.args)))
			})
		except Exception as ex:
			template = "An exception of type {0} occured. Arguments:\n{1}"
			message = template.format(type(ex).__name__, " ".join(ex.args))
			self.set_status(400)
			self.write_json({"error": message})


# endregion


url_paths = [
	# Miscellaneous
	(r'/', PathsUrl),
	(r'/robot\.json', IndexHandler),
	(r'/ip\.json', LocalIp),

	# Motors
	(r'/motors/list\.json', MotorsListHandler),
	(r'/motors/aliases/list\.json', MotorsAliasesListHandler),
	(r'/motors/(?P<alias>[a-zA-Z0-9_]+)/?list\.json', MotorsListHandler),
	(r'/motors/(?P<motor_name>[a-zA-Z0-9_]+)/registers/list\.json', MotorRegistersListHandler),
	(r'/motors/(?P<motor_name>[a-zA-Z0-9_]+)/registers/(?P<register_name>[a-zA-Z0-9_]+)/value\.json',
	 MotorRegisterHandler),
	(r'/motors/registers/(?P<register_name>[a-zA-Z0-9_]+)/list\.json', RegisterValuesHandler),
	(r'/motors/(?P<motor_name>[a-zA-Z0-9_]+)/goto\.json', MotorGotoHandler),
	(r'/motors/goto\.json', MotorsGotoHandler),

	# Sensors
	(r'/sensors/list\.json', SensorsListHandler),
	(r'/sensors/(?P<sensor_name>[a-zA-Z0-9_]+)/registers/list\.json', SensorRegistersListHandler),
	(r'/sensors/(?P<sensor_name>[a-zA-Z0-9_]+)/registers/(?P<register_name>[a-zA-Z0-9_]+)/value\.json',
	 SensorRegisterHandler),
	(r'/sensors/camera/frame\.png', CameraHandler),
	(r'/sensors/code/(?P<code_name>[a-zA-Z0-9_]+)\.json', MarkerDetectorHandler),

	# Moves
	(r'/records/list\.json', ListRecordedMovesHandler),
	(r'/records/(?P<move_name>[a-zA-Z0-9_]+)/value\.json', MoveHandler),
	(r'/records/(?P<move_name>[a-zA-Z0-9_]+)/record\.json', RecordMoveHandler),
	(r'/records/(?P<move_name>[a-zA-Z0-9_]+)/save\.json', SaveMoveHandler),
	(r'/records/(?P<move_name>[a-zA-Z0-9_]+)/play\.json', PlayMoveHandler),
	(r'/records/(?P<move_name>[a-zA-Z0-9_]+)/stop\.json', StopMoveHandler),
	(r'/records/(?P<move_name>[a-zA-Z0-9_]+)/delete\.json', DeleteMoveHandler),

	# Primitives
	(r'/primitives/list\.json', PrimitivesListHandler),
	(r'/primitives/running/list\.json', RunningPrimitivesListHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/start\.json', StartPrimitiveHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/stop\.json', StopPrimitiveHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/pause\.json', PausePrimitiveHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/resume\.json', ResumePrimitiveHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/properties/list\.json', PrimitivePropertiesListHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/properties/(?P<prop>[a-zA-Z0-9_]+)/value\.json',
	 PrimitivePropertyHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/methods/list\.json', ListPrimitiveMethodsHandler),
	(r'/primitives/(?P<primitive_name>[a-zA-Z0-9_]+)/methods/(?P<method_name>[a-zA-Z0-9_]+)/args\.json',
	 CallPrimitiveMethodHandler),

	# Ik
	(r'/ik/(?P<chain_name>[a-zA-Z0-9_]+)/value\.json', IKValueHandler),
	(r'/ik/(?P<chain_name>[a-zA-Z0-9_]+)/goto\.json', IKGotoHandler),
	(r'/ik/(?P<chain_name>[a-zA-Z0-9_]+)/rpy\.json', IKRPYHandler)
]


class HTTPRobotServer(AbstractServer):
	"""Refer to the REST API for an exhaustive list of the possible routes."""

	def __init__(self, robot, host='0.0.0.0', port='8080', cross_domain_origin='*', **kwargs):
		AbstractServer.__init__(self, robot, host, port)

	def make_app(self):
		PoppyRequestHandler.restful_robot = self.restful_robot
		return Application(url_paths)

	def run(self, **kwargs):
		""" Start the tornado server, run forever"""

		try:
			loop = IOLoop()
			app = self.make_app()
			app.listen(self.port)
			loop.start()

		except socket.error as sErr:
			# Re raise the socket error if not "[Errno 98] Address already in use"
			if sErr.errno != errno.EADDRINUSE:
				raise sErr
			else:
				logger.warning(
					'The webserver port {} is already used. May be the HttpRobotServer is already running or another '
					'software is using this port.'.format(self.port))

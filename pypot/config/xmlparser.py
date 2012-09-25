import xml.dom.minidom

import pypot.dynamixel
import pypot.robot

# MARK: - Robot configuration

def load_robot_configuration(filepath):
    """ Parses a specified robot configuration xml file and creates a :py:class:`~pypot.robot.Robot`. """
    dom = xml.dom.minidom.parse(filepath)
    return _handle_robot(dom)


def _handle_robot(dom):
    """ Parses the <Robot> element of an xml file and returns a :py:class:`~pyrobot.robot.Robot`. """
    robot_node = dom.getElementsByTagName("Robot")[0]

    name = robot_node.getAttribute("name")

    eeprom_node = robot_node.getElementsByTagName("EEPROM")[0]
    eeprom_values = _handle_eeprom(eeprom_node)

    controller_nodes = dom.getElementsByTagName("DynamixelController")
    controllers = [_handle_controller(c) for c in controller_nodes]

    motors = sum(map(lambda c: c.motors, controllers), [])

    robot = pypot.robot.Robot(name, motors, controllers, eeprom_values)

    return robot

def _handle_controller(controller_node):
    """ Parses the <DynamixelController> element and returns a :py:class`~pypot.dynamixel.DynamixelController`.  """
    controller_type = controller_node.getAttribute("type")
    controller_port = controller_node.getAttribute("port")

    alarm_node = controller_node.getElementsByTagName("AlarmBlackList")[0]
    alarms = map(lambda node: node.tagName,
                 filter(lambda child: child.nodeType == alarm_node.ELEMENT_NODE, alarm_node.childNodes))
    
    motor_nodes = controller_node.getElementsByTagName("DynamixelMotor")
    motors = [_handle_motor(m) for m in motor_nodes]
    
    controller = pypot.dynamixel.DynamixelController(controller_port, controller_type, motors,
                                                     blacklisted_alarms=alarms)
    
    return controller


def _handle_motor(motor_node):
    """ Parses the <DynamixelMotor> and returns a :py:class:`~pypot.dynamixel.DynamixelMotor`. """
    motor_name = motor_node.getAttribute("name")
    motor_id = int(motor_node.getAttribute("id"))
    motor_type = motor_node.getAttribute("type")
    motor_orientation = motor_node.getAttribute("orientation")
    motor_is_direct = True if motor_orientation == "direct" else False
    motor_offset = float(motor_node.getAttribute("offset"))
    
    custom_eeprom = _handle_eeprom(motor_node)
    
    motor = pypot.dynamixel.DynamixelMotor(motor_id, motor_name, motor_type,
                                           motor_is_direct, motor_offset,
                                           **custom_eeprom)

    return motor

def _handle_eeprom(node):
    """ Parses the eeprom elements of a node and returns a dict of those values. """
    elements = filter(lambda child: child.nodeType == node.ELEMENT_NODE,
                      node.childNodes)
    
    return dict([(el.tagName, eval(el.firstChild.data)) for el in elements])   

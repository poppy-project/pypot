# Pypot REST APIs

The pypot library provides a REST API which can be used to access the [Robot](http://poppy-project.github.io/pypot/pypot.robot.html) level and all its attached [motors](http://poppy-project.github.io/pypot/pypot.robot.html#module-pypot.robot.motor), [sensors](http://poppy-project.github.io/pypot/pypot.robot.html#module-pypot.robot.sensor), and [primitives](http://poppy-project.github.io/pypot/pypot.primitive.html). Through the REST API, you can:
* **Motors**
  * get the motors list and get/set value from/to their registers
* **Sensors**:
  * get the sensors list and get/set value from/to their registers
* **Primitives**:
  * get the primitives list (running or not), start, stop, pause, and resume them.
  * you can also access their publicly available properties and methods.

*Note that only the defined as **publicly available** registers or methods will be accessed through the REST API. Please refer to the [note for developers](#markdown-header-note-for-developers) below for details.*

# REST APIs

*Please note that all answers are always sent as json dictionary.*

## Robot

### Motor

|  | HTTP | JSON | Example of answer |
|--------------------------------------------|:------------------------------------------------------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------:|------------------------------------------------------------------------|
| Get the motors list | GET /motor/list.json | {"robot": {"get_motors_list": {"alias": "motors"}}} | {'motors': ["l_elbow_y", "r_elbow_y", "r_knee_y", "head_y", "head_z"]} |
| Get the motors alias list | GET /motor/alias/list.json | {"robot": {"get_motors_alias": {}}} | {'alias': ["r_leg", "torso", "l_leg_sagitall"]} |
| Get the motors list of a specific alias | GET /motor/\<alias>/list.json | {"robot": {"get_motors_list": {"alias": "<alias>"}}} | {<alias>: ["l_elbow_y", "r_elbow_y", "r_knee_y", "head_y", "head_z"]} |
| Get the registers list of a specific motor | GET /motor/\<motor_name>/register/list.json | {"robot": {"get_registers_list": {"motor": "<motor_name>"}}} | {'registers': ["goal_speed", "compliant", "present_load", "id"]} |
| Get the register value | GET /motor/\<motor_name>/register/\<register_name> | {"robot": {"get_register_value": {"motor": "<motor_name>", "register": "<register_name>"}}} | {"present_position": 30} |
| Set new value to a register | POST /motor/\<motor_name>/register/\<register_name>/value.json | {"robot": {"set_register_value": {"motor": "<motor_name>", "register": "<register_name>", "value": {"arg1": "val1", "arg2": "val2", "...": "..."}}} | {} |

### Sensor

*Similar to the motor API. You just replace motor by sensor (for the moment there is no alias for sensors).*

## Primitive

|  | HTTP | JSON | Example of answer |
|-----------------------------------|:-------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------------------:|:----------------------------------------------------------------------:|
| Get the primitives list | GET /primitive/list.json | {"robot": {"get_primitives_list": ""}} | {'primitives': ["stand_up", "sit", "head_tracking"]} |
| Get the running primitives list | GET /primitive/running/list.json | {"robot": {"get_running_primitives_list": ""}} | {'primitives': ["head_tracking"]} |
| Start a primitive | GET /primitive/\<prim>/start.json | {"robot": {"start_primitive": {"primitive": "<prim>"}}} | {} |
| Stop a primitive | GET /primitive/\<prim>/stop.json | {"robot": {"stop_primitive": {"primitive": "<prim>"}}} | {} |
| Pause a primitive | GET /primitive/\<prim>/pause.json | {"robot": {"pause_primitive": {"primitive": "<prim>"}}} | {} |
| Resume a primitive | GET /primitive/\<prim>/resume.json | {"robot": {"resume_primitive": {"primitive": "<prim>"}}} | {} |
| Get the primitive properties list | GET /primitive/\<prim>/property/list.json | {"robot": {"get_primitive_properties_list": {"primitive": "<prim>"}}} | {"property": ["filter", "smooth"]} |
| Get a primitive property value | GET /primitive/\<prim>/property/<prop> | {"robot": {"get_primitive_property": {"primitive": "<prim>", "property": "<prop>"}}} | {"sin.amp": 30.0} |
| Set a primitive property value | POST /primitive/\<prim>/property/<prop>/value.json | {"robot": {"set_primitive_property": {"primitive": "<prim>", "property": "<prop>", "args": {"arg1": "val1", "arg2": "val2", "...": "..."}}}} | {} |
| Get the primitive methods list | GET /primitive/\<prim>/method/list.json | {"robot": {"get_primitive_methods_list": {"primitive": "<prim>"}}} | {"methods": ["get_tracked_faces", "start", "stop", "pause", "resume"]} |
| Call a method of a primitive | POST /primitive/\<prim>/method/\<meth>/args.json | {"robot": {"call_primitive_method": {"primitive": "<prim>", "method": "<meth>", "args": {"arg1": "val1", "arg2": "val2", "...": "..."}}}} |  |


## Note for developers

In order to **publicly** available through the REST API, the registers of the motors/sensors and the properties/methods of the primitives should be added to specific lists.

More precisely, the [Motor](http://poppy-project.github.io/pypot/pypot.robot.html#pypot.robot.motor.Motor) class sets the [registers](http://poppy-project.github.io/pypot/pypot.dynamixel.html#pypot.dynamixel.motor.DxlMotor.registers) list (similarly for the [Sensor](http://poppy-project.github.io/pypot/pypot.sensor.html) class) and the [Primitives](http://poppy-project.github.io/pypot/pypot.primitive.html#pypot.primitive.primitive.Primitive) uses the [methods]() and [properties]() list.

Those are class variables and can be extended when defining your own subclasses (see the [Sinus primitive](https://github.com/poppy-project/pypot/blob/REST-API-2.0/pypot/primitive/utils.py) as an example).

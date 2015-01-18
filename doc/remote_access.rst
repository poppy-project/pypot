REST API
========

We add the possibility to remotely access and control your robot through TCP network. This can be useful both to work with client/server architecture (e.g. to separate the low-level control running on an embedded computer and higher-level computation on a more powerful computer) and to allow you to plug your existing code written in another language to the pypot's API.

We defined a protocol which permits the access of all the robot variables and method (including motors and primitives) via a JSON request. The protocol is entirely described in the section :ref:`remote_protocol` below. Two transport methods have been developed so far:

* HTTP via GET and POST request (see the :ref:`http_server` section)
* ZMQ socket (see the :ref:`zmq_server` section)

The :class:`~pypot.server.request.BaseRequestHandler` has been separated from the server, so you can easily add new transport methods if needed.

.. warning:: For the moment, the server is defined as a primitive, so multiple requests will not be automatically combined but instead the last request will win. In further version, it will be possible to spawn each client in a separate primitive.

As an example of what you can do, here is the code of getting the load of a motor and changing its position::

    import zmq

    robot = pypot.robot.from_config(...)

    server = pypot.server.ZMQServer(robot, host, port)
    server.start()

    c = zmq.Context()
    s = c.socket(zmq.REQ)

    req = {
        'get': {motor_name: ('present_load', )},
        'set': {motor_name: {'goal_position': 20.0}}
    }

    s.send_json(req)
    answer = s.recv_json()

.. _remote_protocol:

Protocol
--------

Our protocol allows you define three types of requests:

* :ref:`get_req` (to retrieve a motor register value, access a primitive variable)
* :ref:`set_req` (to set a motor register value, modify any variable within the robot instance)
* :ref:`call_req` (to call a method of any object defined within the robot instance, e.g. a primitive)

An entire request is defined as follows::

    req = {
        'get': get_request,
        'set': set_request,
        'call': call_request
    }

.. note:: The field are optional, so you can define a request with only a get field for instance.


.. _get_req:

Get Request
+++++++++++

The get request is constructed as follows::

    get_request = {
        obj_name_1: (var_path_1, var_path_2, ...),
        obj_name_2: (var_path_1, var_path_2, ...),
        ...
    }

.. note:: The var_path can be a complete path such as skeleton.hip.position.x.

For instance, if you write the following get request::

    get_request = {
        'base_tilt_lower': ('present_position', 'present_load'),
        'base_tilt_upper': ('present_temperature', ),
        'dance', ('current_song.filename', ) # Where dance is an attached primitive
    }

It will retrieve the variables robot.base_tilt_lower.present_position, robot.base_tilt_lower.present_load, robot.base_tilt_upper.present_temperature, and robot.dance.current_song.

The server will return something like::

    answer = {
        'get': {
            'base_tilt_lower': {'present_position': 10.0, 'present_load': 23.0},
            'base_tilt_upper': {'present_temperature': 40},
            'dance': {'current_song.filename': 'never_gonna_give_you_up.mp3'}
        }
    }


.. _set_req:

Set Request
+++++++++++

The set request is really similar to the get request. Instead of giving a list of the var_path you want to access, you provide dictionary of (var_path: desired_value)::

    set_request = {
        obj_name_1: {var_path_1: value1, var_path_2: value2, ...},
        obj_name_2: {var_path_1: value1, var_path_2: value2, ...},
        ...
    }

The server will return an empty set field used as an acknowledgment::

    answer = {
        'set': None,
    }

.. _call_req:

Call Request
++++++++++++

You can also build call request as follows::

    call_request = {
        obj_name_1: {meth_name_1: args, meth_name_2: args, ...},
        obj_name_2: {meth_name_1: args, meth_name_2: args, ...},
        ...
    }

.. note:: The argument as passed as a list.


For instance, this request will start the dance primitive::

    call_request = {
        'dance', {'start': ()} # The start method does not take any argument so we pass the empty list.
    }

The server will return the result of the called methods::

    answer = {
        'call': {
            'dance': {'start': None}, # The start methods does not return anything.
        }
    }

.. _zmq_server:

Zmq Server
----------

The Zmq Server used a Zmq socket to send (resp. receive) JSON request (JSON answer). It is based on the REQ/REP pattern. So you should always alternate sending and receiving. It will probably be switched to PUB/SUB soon.

Zmq has been chosen as it has been `binded to most language <http://zeromq.org/bindings:_start>`_ and can thus be used to connect code from other language to pypot. For instance, we used it to connect `RLPark <http://rlpark.github.io>`_ (a Java reinforcement learning library) to pypot.

Here is an example of how you can create a zmq server and send request::

    import zmq

    robot = pypot.robot.from_config(...)

    server = pypot.server.ZMQServer(robot, host, port)
    server.start()

    c = zmq.Context()
    s = c.socket(zmq.REQ)
    s.connect('tcp://{}:{}'.format(host, port))

    req = {
        'get': {motor_name: ('present_load', )},
        'set': {motor_name: {'goal_position': 20.0}}
    }

    s.send_json(req)
    answer = s.recv_json()

.. note:: The zmq server is faster than the HTTP version and should be preferred when working with high frequency control loops.

.. _http_server:

Http Server
-----------

The HTTPServer is based on the bottle python framework (http://bottlepy.org/). We have developed a sort of REST API based on the protocol described above:

* GET /motor/list.json
* GET /primitive/list.json
* GET /motor/<name>/register.json (or GET /<name>/register.json)
* GET /motor/<name>/<register> (or GET /<name>/<register>)
* POST /motor/<name>/<register> (or POST /<name>/<register>)
* POST /primitive/<prim_name>/call/<meth_name> (or GET /<prim_name>/call/<meth_name>)
* POST /request.json

An example of how you can use the HTTP server::

    import urllib2
    import json
    import time

    import pypot.robot
    import pypot.server

    robot = pypot.robot.from_config(...)

    server = pypot.server.HTTPServer(robot, host, port)
    server.start()

    time.sleep(1) # Make sure the server is really started

    url = 'http://{}:{}/motor/list.json'.format(host, port)
    print urllib2.urlopen(url).read()

    url = 'http://{}:{}/motor/base_tilt_lower/goal_position'.format(host, port)
    data = 20.0
    r = urllib2.Request(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    print urllib2.urlopen(r).read()

.. note:: Note that the http server will always return a dictionary (see http://haacked.com/archive/2009/06/24/json-hijacking.aspx for an explanation).

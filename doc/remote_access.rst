REST API
========

We add the possibility to remotely access and control your robot through TCP network. This can be useful both to work with client/server architecture (e.g. to separate the low-level control running on an embedded computer and higher-level computation on a more powerful computer) and to allow you to plug your existing code written in another language to the pypot's API.

We defined a protocol which permits the access of all the robot variables and method (including motors and primitives) via a JSON request. The protocol is entirely described in the section :ref:`remote_protocol` below. Two transport methods have been developed so far:

* HTTP via GET and POST request (see the :class:`~pypot.server.httpserver.HTTPRobotServer`)
* ZMQ socket (see the :class:`~pypot.server.zmqserver.ZMQRobotServer`)

The :class:`~pypot.server.rest.RESTRobot` has been abstracted from the server, so you can easily add new transport methods if needed.

As an example of what you can do, here is the code of getting the load of a motor and changing its position using ZMQ socket::

    import zmq
    import threading

    robot = pypot.robot.from_config(...)

    server = pypot.server.ZMQServer(robot, host, port)
    # We launch the server inside a thread
    threading.Thread(target=lambda: server.run()).start()

    c = zmq.Context()
    s = c.socket(zmq.REQ)

    req = {"robot": {"get_register_value": {"motor": "m2", "register": "present_load"}}}
    s.send_json(req)
    answer = s.recv_json()
    print(answer)

    req = {"robot": {"set_register_value": {"motor": "m2", "register": "goal_position", "value": 20}}}
    s.send_json(req)
    answer = s.recv_json()
    print(answer)

Equivalent example using urllib in Python to send http requests::

    import urllib, urllib2, json

    #make a GET request to read the names of all motors
    allmotors= urllib2.urlopen("http://poppy.local:8080/motor/list.json").read()
    print allmotors

    #transform json into Python dictionnary
    allmotors_dict = json.loads(allmotors)
    for m in allmotors_dict["motors"]:
        print m

    #make POST request to move a motor
    url = 'http://poppy.local:8080/motor/head_z/register/goal_position/value.json'
    values = json.dumps(-20)
    req = urllib2.Request(url, values)
    req.add_header("Content-Type",'application/json')
    response = urllib2.urlopen(req)


.. _remote_protocol:

Protocol
--------

The entire protocol is entirely described `here <https://github.com/poppy-project/pypot/blob/master/REST-APIs.md>`_.

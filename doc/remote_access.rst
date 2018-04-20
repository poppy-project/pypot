REST API
========

We add the possibility to remotely access and control your robot through TCP network. This can be useful both to work with client/server architecture (e.g. to separate the low-level control running on an embedded computer and higher-level computation on a more powerful computer) and to allow you to plug your existing code written in another language to the pypot's API.

We defined a protocol which permits the access of all the robot variables and method (including motors and primitives) via a JSON request. The protocol is entirely described in the section :ref:`remote_protocol` below. Two transport methods have been developed so far:

* HTTP via GET and POST request (see the :class:`~pypot.server.httpserver.HTTPRobotServer`)
* ZMQ socket (see the :class:`~pypot.server.zmqserver.ZMQRobotServer`)

The :class:`~pypot.server.rest.RESTRobot` has been abstracted from the server, so you can easily add new transport methods if needed.

As an example of what you can do, here is the code of getting the load of a motor and changing its position::

    ### ON THE ROBOT START THE ZMQ SERVER:

    poppy-services -vv --zmq poppy-ergo-jr
    # (but substitute "poppy-ergo-jr" for the name of your robot)

    ### THEN ON THE REMOTE PC RUN THIS SCRIPT:

    import pypot
    import zmq

    ROBOT1 = "flogo4.local"  # <--- your robot's IP or hostname
    PORT = 5757 # the IP of the robot's ZMQ server. This is fixed

    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    print ("Connecting to server...")
    socket.connect ("tcp://{}:{}".format(ROBOT1, PORT))
    print ("Connected.")


    ## get the value of one register of one specific motor (in this case the current load on motor 2)
    req = {"robot": {"get_register_value": {"motor": "m2", "register": "present_load"}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)


    ## get all the register names of a given motor
    req = {"robot": {"get_motor_registers_list": {"motor": "m2"}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)


    ## get all the current positions and current angular velocity
    req = {"robot": {"get_pos_speed": {}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)


    ## set all motors to a given angle (example: Ergo jr)
    req = {"robot": {"set_pos": {"pos":[0, 0, 0, 0, 0, 0]}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)


    ## set one motor to a given angle
    req = {"robot": {"set_register_value": {"motor": "m1", "register": "goal_position", "value": "20"}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)

.. _remote_protocol:

Protocol
--------

The entire protocol is entirely described `here <https://github.com/poppy-project/pypot/blob/master/REST-APIs.md>`_.

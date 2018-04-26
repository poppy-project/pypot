## How to use the fast ZMQ protocol for remote-controlling the Poppy Ergo Jr

### Installation

SSH into your poppy.

    # NAME is the name of the robot, and by default "poppy"
    ssh poppy@[NAME].local 

Uninstall the system PyPot package.

    pip uninstall pypot
    
Make a new directory and git clone this repo.

    mkdir tools
    cd tools
    git clone https://github.com/fgolemo/pypot.git
    
Install the new package

    cd pypot
    pip install -e .
    
### Start the server

SSH into the robot, if you haven't already.

\[ONLY ONCE PER ROBOT RESTART\] Kill the existing motor control process:

    fuser -k /dev/ttyA*
    
Start the server process

    poppy-services -vv --zmq poppy-ergo-jr
    
That's it. The robot should say something like "Attempt 1 to start the server. ... Robot up and running."

You can kill this server (either by logging out or via CTRL+c) and start it again, but you don't have to do `fuser` again.

### Connect ot the server and control the robot

On your PC you don't need any Python packages other than `zmq`.

Use the following code for reading the servo sensors or setting the goal positions of the robot:

    import zmq
    
    ROBOT1 = "flogo4.local" # name of your robot
    PORT = 5757


    ## ESTABLISH ROBOT CONNECTION    
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    print ("Connecting to server...")
    socket.connect ("tcp://{}:{}".format(ROBOT1, PORT))
    print ("Connected.")
    
    
    ## READ THE VALUE OF A SINGLE MOTOR, SINGLE REGISTER
    req = {"robot": {"get_register_value": {"motor": "m2", "register": "present_load"}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)
    
    
    ## GET THE LIST OF ALL REGISTERS FOR A MOTOR
    req = {"robot": {"get_motor_registers_list": {"motor": "m2"}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)

    
    ## GET ALL MOTOR POSITIONS (6 values) AND VELOCITIES (6 values) 
    ## IN A 12 ELEMENT ARRAY    
    req = {"robot": {"get_pos_speed": {}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)


    ## SET ALL MOTORS TO AN ANGLE (in degrees)
    req = {"robot": {"set_pos": {"positions":[0, 0, 0, 0, 0, 0]}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer) # the answer should be empty "{}"
    
    
    ## SET THE REGISTER OF A SINGLE MOTOR TO A VALUE (value must be string in Python 3)
    req = {"robot": {"set_register_value": {"motor": "m1", "register": "goal_position", "value": "20"}}}
    socket.send_json(req)
    answer = socket.recv_json()
    print(answer)


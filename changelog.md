# Changelog

## V 2.11

## Features
* Add dummy motors (mostly for unittest)
* add native support for the pixl board
* allow to disable sensor at loading (convenient for camera sensor)
* add a dummy camera
* Add support for RX-24 dynamixel motors
* Add an event used to check if a "loopable" thread has been updated
* Move can now be plotted using matplotlib

### Snap
* Add blocs: “ping url <hostname>” and “set $robot host to <hostname>” which aim to fix DNS issues in some filtered networks.
* update “set <register> of motor(s) <motors> to value <value>” : speed register is now moving_speed instead of goal_speed. Able to use it through many motors at once now
* fix “get  <register> of motor(s) <motors>”
* fix some default values of inputs variable for consistency
* add entry for ik in SnapRemoteServer
* check return-delay-time at startup to prevent timeouts with misconfigured motors

## Bugfix
* many primitives threading issues
* python >= 3.4 compatibility issues
* setup unittest via dummy robot
* fix the unclear exception "Cannot unpack *values"
* fix cli tool `poppy-motor-reset` and rename it to `dxl-config`
* Fix deprecation issue in get_control_table
* Clear error when there is no "time script" in a v-rep scene
* Fix a freeze when stopping a paused primitive
* Fix offset/orientation issue in DummyController
* Fix hostname resolution
* Make initialization of synchronization loop more robust


## V 2.10
### Features
* add support for led inside primitive (XL320)
* remove RPICam and use v4l driver in opencv
* support hampy marker in Snap!

### Fix
* network issue for finding local ip when there is no interface
* Python 3.5 compatibility



## V 2.9
### Image feature Sensors
* face
* blob
* qrcode

### LED register for XL-320 motors
### various bug fixes

## V 2.8
### Sync Loop
* possibility to define synchronous loop
* define a "light" synchronization loop
* can now choose sync. loop inside the config

### Better Sensor Integration
* can specify sensor inside the config file

## V 2.1
* now uses the poppy_creature package
* add support for present_load/torque_limit/compliant in V-REP
* fix a bug when using setup.py install
* add minimum jerk of Steve N'Guyen
* add safe compliance behavior
* add camera sensor based on opencv

## V. 2.0

### Major changes
* support for V-REP simulator
* new controller implementation: [extending pypot](http://poppy-project.github.io/pypot/extending.html)

### Minor changes
* Use of descriptors for motor registers
* REST API / remote robot
* Starts automatically the synchronization


## V. 1.7

### Minor changes
* Autodetect robot

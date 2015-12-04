# Changelog

# V 2.10
## Features
* add support for led inside primitive (XL320)
* remove RPICam and use v4l driver in opencv
* support hampy marker in Snap!

## Fix
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

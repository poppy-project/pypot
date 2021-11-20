[![PyPI](https://img.shields.io/pypi/v/pypot.svg)](https://pypi.python.org/pypi/pypot/)
[![Build Status](https://github.com/poppy-project/pypot/actions/workflows/test_and_distribute.yml/badge.svg)](https://github.com/poppy-project/pypot/actions)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.591809.svg)](https://doi.org/10.5281/zenodo.591809)



# Pypot ⚙️ A Python library for Dynamixel motor control 

Pypot is a cross-platform Python library making it easy and fast to control custom robots based on multiple models of Dynamixel motors. Use Pypot to:

* control Robotis motors through USB2Dynamixel, USB2AX or [Pixl 4 Raspberry Pi](https://github.com/poppy-project/pixl) devices,
* define kinematic chains of a custom robot and control it through high-level commands (Forward & Inverse Kinematics),
* define primitives (motions applying to motor groups) and easily combine them to create custom complex behaviors (Robot dance, arm shaking, writing with a pen...).
* define sensor access and processing (QRCode detection, force sensors, RGB-D, ...)

Pypot is also compatible with the [CoppeliaSim simulator](http://www.coppeliarobotics.com) (formerly V-REP), embeds a [REST API](https://docs.poppy-project.org/en/programming/rest.html) for Web-based control, and supports visual programming via [Scratch](https://docs.poppy-project.org/en/getting-started/program-the-robot.html#using-scratch) and [Snap](https://docs.poppy-project.org/en/getting-started/program-the-robot.html#using-snap).

## 🔌 Compatible hardware

**Compatible motors:** MX-106, MX-64, MX-28, MX-12, AX-12, AX-18, RX-24, RX-28, RX-64, XL-320, SR-RH4D, EX-106. Derivated versions are also supported (e.g. MX-28AT, MX-28R, MX-28T, ...). Both protocols v1 and v2 are supported but v2 is used only for XL-320. Use [Herborist](https://github.com/poppy-project/herborist#herborist) to help detect IDs and baudrates of motors.

**Compatible sensors:** Kinect 1, QRCode from RGB camera, sonar, micro-switch from Raspberry Pi GPIO, digital or analog sensor connected to Arduino

**Compatible interpreters:** Python 3.6, 3.7, 3.8, 3.9

Other models of motors and sensors can be integrated with little effort and time. Other programming languages may be connected through the REST API.

## Read 📖 [Documentation](https://docs.poppy-project.org/en/software-libraries/pypot.html) and get ⁉️ [Assistance](https://forum.poppy-project.org/)

## Pypot is part of the opensource Poppy project

Pypot is part of the [Poppy project](http://www.poppy-project.org) aiming at developing robotic creations that are easy to build, customize, deploy, and share. It promotes open-source by sharing 3D-printed hardware, software, and web tools.

The Poppy creatures are:
* **[Poppy Humanoid](https://www.poppy-project.org/en/robots/poppy-humanoid/)**: a kid-size humanoid robot designed for biped locomotion and physical human-robot interaction (25 DoF) for biped research and university workshops,
* **[Poppy Torso](https://www.poppy-project.org/en/robots/poppy-torso/)**: just the torso of the humanoid robot, with a suction pad to stick it attach it firmly to a desk (13 DoF) for HRI research, university and high school workshops
* **[Poppy Ergo Jr](https://www.poppy-project.org/en/robots/poppy-ergo-jr/)**: a low-cost robotic arm for primary to middle school (6 Dof) for primary or middle school workshops

![Poppy Humanoid](./doc/poppy-creatures.jpg)

All those creatures are based on a combination of standard dynamixel actuators, 3D printed parts and open-source electronics such as Arduino boards. Both the hardware (3D models, electronics...) and software can be freely used, modified and duplicated.

## 💻 Installation

If you are using a Poppy robot embedding a Raspberry Pi, Pypot is already shipped with it. For custom robots, just type ⌨️ `pip install pypot` in your system terminal! 

If you intend to modify or add features to Pypot, create a virtual environment and install it from sources instead:
```bash
git clone https://github.com/poppy-project/pypot
cd pypot/pypot
pip install .
```

Additional drivers may be needed for USB2serial, depending of your OS. Check here:
* [USB2AX](http://www.xevelabs.com/doku.php?id=product:usb2ax:quickstart) - this device is designed to manage TTL communication only
* USB2Dynamixel - this device can manage both TTL and RS485 communication.
* [Pixl board](https://github.com/poppy-project/pixl) for RaspberryPi

## 👨‍💻 Contributing

If this is the first time you contribute to Pypot, it is a good idea to share your work on [the forum](https://forum.poppy-project.org/) first, we will be happy to give you a hand so that you can contribute to the opensource project.

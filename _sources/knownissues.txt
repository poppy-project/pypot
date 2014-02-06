Known Issues
************

For any issue which is not listed here, please report it in our GitHub `issue tracker <https://github.com/poppy-project/pypot/issues>`_. Please give us as detailed information as possible so we can reproduce your bug and hopefully solve it.


Issue with USB2AX driver on Mac OS
----------------------------------

The connection to the device seems to fail. More precisely, we do not receive any message from the motors. A workaround is provided directly in the code. The DxlIO will try to connect until it can ping a motor. Once connected, it does not seem to cause any problem anymore.

USB2Dynamixel driver performance on Mac OS
------------------------------------------

The usb2serial driver seems to have a strong impact on the reachable communication speed with motors. In particular, the USB2Dynamixel while directly working on the most used operating system (tested on Linux, Windows and Mac OS), lead to significantly slower communication on Mac than on other operating system (sending a message could take up to 300ms on MacOS instead of about 5ms on Windows or Linux). Actually, it is more efficient to use PyPot inside a VM running Linux or Windows than directly using it from Mac OS.
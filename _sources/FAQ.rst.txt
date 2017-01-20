FAQ
***

Why is the default baud rate different for robotis and for pypot ?
------------------------------------------------------------------

Robotis motors are set up to work with a 57140 baud rate. Yet, in pypot we choose to use 1000000 baud rate as the default configuration. While everything would work with the robotis default baud rate, we choose to incitate people to modify this default configuration to allow for more performance.

I got a DxlCommunicationError when scanning multiple motors on a bus
--------------------------------------------------------------------

This exception is usually raised when two (or more) motors share the same id. This should never happened, all ids should be unique on a same bus. Otherwise, package will collide resulting in communication error.

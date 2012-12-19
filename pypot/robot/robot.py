import pypot.robot.xmlparser
import pypot.dynamixel.controller

class Robot(object):
    def __init__(self):
        self._dxl_controllers = []

    def _attach_motors(self, dxl_io, dxl_motors):
        self._dxl_controllers.append(pypot.dynamixel.controller.BaseDxlController(dxl_io, dxl_motors))
    
        for m in dxl_motors:
            setattr(self, m.name, m)
        
    def start_sync(self):
        map(lambda c: c.start(), self._dxl_controllers)

    def stop_sync(self):
        map(lambda c: c.stop(), self._dxl_controllers)

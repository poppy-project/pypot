import pypot.dynamixel.controller

class Robot(object):
    def __init__(self, dxl_io, dxl_motors):
        self._dxl_controller = pypot.dynamixel.controller.BaseDxlController(dxl_io, dxl_motors)
    
        for m in dxl_motors:
            setattr(self, m.name, m)
        
    def start_sync(self):
        self._dxl_controller.start()

    def stop_sync(self):
        self._dxl_controller.stop()
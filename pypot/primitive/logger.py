import logging

import pypot.robot
import pypot.primitive

class RobotLogger(pypot.primitive.LoopPrimitive):
    def __init__(self, robot, filemane, log_id='pypotlog', log_frequency=20):
        pypot.primitive.LoopPrimitive.__init__(self, robot, log_frequency)

        self.log_id = log_id

        logging.basicConfig(format='%(log_id)s#%(asctime)s#%(message)s',  
                            filename=filename, 
                            level=logging.INFO)

        self.values = ['name', 'goal_position', 'moving_speed', 'torque_limit', 'pid',
                       'position', 'present_speed', 'present_load', 'present_temperature']

        logging.info(str(self.values), extra={'log_id': self.log_id})

    def update(self):

        logging.info([[getattr(m, name) for name in self.values] for m in robot.motors], 
                        extra={'log_id': self.log_id})
        # Todo log de l'accelero
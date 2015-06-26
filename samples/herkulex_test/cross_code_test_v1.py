
import time
import pypot.robot
import numpy
import pypot.primitive

eligible_ports = {'Herkulex' : ('COM4',),'Dynamixel' : ('COM3',)}
crossfile = 'cross_config_v1.json'

class DancePrimitive(pypot.primitive.Primitive):
    def run(self, amp=30, freq=0.5):
        while self.elapsed_time < 5:
            x = amp * numpy.sin(2 * numpy.pi * freq * self.elapsed_time)
            for m in self.robot.motors:
                m.goto_position(x,0.02)
            time.sleep(0.02)

if __name__ == '__main__':
    test_robot=pypot.robot.from_json(crossfile, eligible_ports)
    test_robot.compliant = False
    dance = DancePrimitive(test_robot)
    dance.start()
    dance.stop()
    test_robot.compliant = True
    test_robot.close()
    print('done!')
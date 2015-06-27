
import time
import pypot.robot
import numpy
import pypot.primitive

eligible_ports = {'Herkulex' : ('COM4',),'Dynamixel' : ('COM3',)}
crossfile = 'hangy_config_v2.json'

neutral_position={'leg1_base' : -90,
            'leg1_joint1' : -80,
            'leg1_joint2' : -45,
            'leg2_base' : -90,
            'leg2_joint1' :-80,
            'leg2_joint2' : -45,
            'puller1' : -90,
            'puller2' : -90}

class SwingPrimitive(pypot.primitive.Primitive):
    def run(self, amp=70, freq=0.25):
        while self.elapsed_time < 5:
            x = -(amp * numpy.sin(2 * numpy.pi * freq * self.elapsed_time + numpy.pi/2)+20)
            for m in self.robot.motors:
                self.robot.leg1_base.goto_position(x,0.02)
                self.robot.leg2_base.goto_position(x,0.02)
            time.sleep(0.02)


if __name__ == '__main__':
    test_robot=pypot.robot.from_json(crossfile, eligible_ports)
    test_robot.compliant = False
    for m in test_robot.motors:
        print('for %s: min %s, max %s, current %s' %(m.name, m.lower_limit, m.upper_limit, m.present_position))
    print('to neutral')
    test_robot.goto_position(neutral_position, 2)
    time.sleep(3)
    for m in test_robot.motors:
        print('for %s: min %s, max %s' %(m.name, m.lower_limit, m.upper_limit))
    swing = SwingPrimitive(test_robot)
    swing.start()
    swing.stop()
    print('to neutral')
    test_robot.goto_position(neutral_position, 2)
    time.sleep(3)
    test_robot.compliant = True
    test_robot.close()
    print('done!')
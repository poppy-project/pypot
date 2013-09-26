import sys
import glob
import time

import PyQt4.QtCore
import PyQt4.QtGui
import PyQt4.uic


import pypot.robot
import pypot.robot.move as move
import poppy_platform.behavior.upright_posture as upp
import poppy_platform.behavior.move_generator as gen
import poppy_platform.tools.kinematics as kin


motor_to_motor = {
    'Head': 'head',
    'Torso': 'torso',
    'Left Arm': 'l_arm',
    'Right Arm': 'r_arm',
    'Left Leg': 'l_leg',
    'Right Leg': 'r_leg',
    }


class RecorderApp(PyQt4.QtGui.QApplication):
    def __init__(self, argv):
        PyQt4.QtGui.QApplication.__init__(self, argv)
        self.window =  PyQt4.uic.loadUi('recorder.ui')

        self.window.record_button.pressed.connect(self.start_recording)
        self.window.stop_button.pressed.connect(self.stop_recording)
        self.window.play_button.pressed.connect(self.play_move)
        self.window.stop_button_2.pressed.connect(self.stop_move)

        for i in range(len(self.window.motor_group_list)):
            if i in (2, 3):
                continue
            self.window.motor_group_list.item(i).setCheckState(False)

        self.scan_moves()
            
        self.poppy = pypot.robot.from_configuration('../../poppy_platform/configuration/poppyV12.xml')
        self.poppy.start_sync()

        for m in self.poppy.motors:
            m.compliant = False

        stance = upp.UprightPosture(self.poppy)
        self.poppy.attach_primitive(stance, 'stance')
        self.poppy.stance.start()
        
        period=1.3        
        # walking_demo = gen.MoveFromMat(self.poppy, '../../poppy_platform/moves/biowalk.mat', period, gain=0.5)
        # self.poppy.attach_primitive(walking_demo, 'walking_demo')

        self.mp = []


    def start_recording(self):
        self.window.stop_button.setEnabled(True)
        self.window.record_button.setEnabled(False)

        motors = sum([getattr(self.poppy, name) for name in self.motor_group], [])
        
        if self.window.compliant_box.checkState():
            for mm in motors:
                mm.compliant = True

        time.sleep(0.5)
        
        self.recorder = move.LoopMoveRecorder(self.poppy, 50, motors, True)
        self.recorder.start()

    def stop_recording(self):
        self.window.stop_button.setEnabled(False)
        self.window.record_button.setEnabled(True)

        filename = 'moves/{}.move'.format(str(self.window.filename_field.text()))
        self.recorder.stop()
        self.recorder.move.save(filename)
        self.scan_moves()

        self.poppy.stance.start()
        

    def play_move(self):
        names = self.selected_move()
        if not names:
            return

        self.window.stop_button_2.setEnabled(True)
        self.window.play_button.setEnabled(False)
 


        for name in names:
            # if name == 'walk':
            #     self.poppy.walking_demo.start()
            #     continue

            m = move.Move.load('moves/{}.move'.format(name))

            for mm in self.poppy.motors:
                mm.compliant = False
            time.sleep(0.4)
            
            bob = move.MovePlayer(self.poppy, m)
            bob.play()
            self.mp.append(bob)

    def stop_move(self):
        for bob in self.mp:
            bob.stop()
        self.mp = []
        # self.poppy.walking_demo.stop()

        self.window.play_button.setEnabled(True)
        self.window.stop_button_2.setEnabled(False)

        time.sleep(0.5)

        self.poppy.stance.start()
        

    @property
    def motor_group(self):
        groups = []
        for i in range(len(self.window.motor_group_list)):
            checkbox = self.window.motor_group_list.item(i)
            if checkbox.checkState() == 2:
                groups.append(motor_to_motor[str(checkbox.text())])
        return groups

    def selected_move(self):
        i = (self.window.move_list.selectedItems())
        if not i:
            return []
        return [ii.text() for ii in i]
    

    def scan_moves(self):
        names = glob.glob('moves/*.move')
        names = map(lambda s: s.split('/')[-1].replace('.move', ''), names)

        names.append('walk')

        b = True if names else False            
        self.window.move_list.setEnabled(b)
        self.window.loop_box.setEnabled(b)
        self.window.play_button.setEnabled(b)

        if names:
            self.window.move_list.clear()
            for name in names:
                self.window.move_list.addItem(name)

if __name__ == '__main__':
    app = RecorderApp(sys.argv)
    app.window.show()
    sys.exit(app.exec_())

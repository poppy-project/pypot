import sys
import time
import threading

import PyQt4.uic
import PyQt4.QtGui
import PyQt4.QtCore

sys.path.append('../..')
import pypot.dynamixel


# TODO
#    - changer l'id
#    - drag and drop pour changer le baudrate
#    - editer la valeur pos, angle limits... directement dans le label

_dxl_io = None
def get_dxl_connection(port, baudrate):
    global _dxl_io
    if _dxl_io:
        _dxl_io.close()
    
    _dxl_io = pypot.dynamixel.DynamixelIO(port, baudrate, 1.0, blacklisted_alarms=('ANGLE_LIMIT_ERROR',))
    return _dxl_io

dxl_lock = threading.Lock()

class UpdatePositionThread(threading.Thread):
    def __init__(self, port, baudrate, mid, dial):
        threading.Thread.__init__(self)
        self.daemon = True
        self.live = True
        
        self.mid = mid
        self.port = port
        self.baudrate = baudrate
        self.dial = dial
        self.pause = False
    
    def run(self):
        dxl_io = None
        
        while self.live:
            dxl_lock.acquire()
            
            if not dxl_io or not dxl_io.is_open():
                dxl_io = get_dxl_connection(self.port, self.baudrate)
            
            pos = dxl_io.get_current_position(self.mid)
            self.dial.setValue(pos)
            
            dxl_lock.release()
            time.sleep(0.1)

class ScanThread(threading.Thread):
    def __init__(self, port, baudrates, id_range,
                 progress_bar, delegate=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.live = True
        
        self.ids = {}
        
        self.port = port
        self.baudrates = baudrates
        self.id_range = id_range
        
        self.progress_bar = progress_bar
        self.delegate = delegate
    
    def stop(self):
        self.live = False
    
    def notify(self):
        if self.delegate and hasattr(self.delegate, 'done_scanning'):
            self.delegate.done_scanning(self.ids)

    def run(self):
        step = 0
        max_step = len(self.baudrates) * len(self.id_range)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(max_step)
        
        dxl_lock.acquire()
        for b in self.baudrates:
            dxl_io = get_dxl_connection(self.port, b)
            
            self.ids[b] = []
            for mid in self.id_range:
                if dxl_io.ping(mid):
                    model = dxl_io.get_model(mid)
                    self.ids[b].append((mid, model))
                
                step += 1
                self.progress_bar.setValue(step)
                
                if not self.live:
                    self.progress_bar.setValue(max_step)
                    dxl_lock.release()
                    self.notify()
                    return
        
        dxl_lock.release()
        self.notify()


class HerboristApp(PyQt4.QtGui.QApplication):
    def __init__(self, argv):
        PyQt4.QtGui.QApplication.__init__(self, argv)
        
        self.window =  PyQt4.uic.loadUi('herborist.ui')
        
        self.window.scan_button.pressed.connect(self.start_scanning)
        self.window.abort_button.pressed.connect(self.abort_scanning)
        self.window.motor_tree.itemSelectionChanged.connect(self.motors_selected)
        self.window.torque_checkBox.stateChanged.connect(self.toggle_torque)
        self.window.goal_dial.valueChanged.connect(self.goal_position_changed)
        self.window.eeprom_button.pressed.connect(self.update_eeprom)
        self.window.reset_button.pressed.connect(self.reset_eeprom_values)
        
        bg_refresh_ports = threading.Thread(target=self.refresh_ports_list, args=())
        bg_refresh_ports.daemon = True
        bg_refresh_ports.start()
        
        self.update_position_thread = None
        
        for i in range(1, len(self.window.baud_checkboxes)):
            self.window.baud_checkboxes.item(i).setCheckState(False)

    
    def refresh_ports_list(self):
        while True:
            ports = pypot.dynamixel.get_available_ports()
            
            old_ports = []
            for i in range(len(self.window.ports_list_combobox)):
                old_ports.append(str(self.window.ports_list_combobox.itemText(i)))
            
            if ports != old_ports:
                self.window.ports_list_combobox.clear()
                self.window.ports_list_combobox.addItems(ports)
                self.window.ports_list_combobox.update()
                
                self.port = ports[0] if len(ports) else ''
            
            time.sleep(0.5)
    
    def start_scanning(self):
        if hasattr(self, 'st') and self.scan_thread.isAlive:
            self.scan_thread.stop()
        
        port = self.get_port()
        baudrates = self.get_baudrates()
        id_range = self.get_id_range()
        
        if port and baudrates and id_range:
            self.window.motor_tree.clear()
            self.window.motor_tree.setEnabled(False)
            for i in range(len(self.window.motor_gridLayout)):
                self.window.motor_gridLayout.itemAt(i).widget().setEnabled(False)
            
            self.scan_thread = ScanThread(port, baudrates, id_range,
                                          progress_bar=self.window.scan_progressBar,
                                          delegate=self)
            self.scan_thread.start()
            
            self.window.scan_button.setEnabled(False)
            self.window.abort_button.setEnabled(True)
            self.disable_motor_view()
    
    def done_scanning(self, ids):
        self.ids = ids
        
        self.refresh_motor_tree()
        
        self.window.motor_tree.setEnabled(True)
        self.window.scan_button.setEnabled(True)
        self.window.abort_button.setEnabled(False)
    
    def abort_scanning(self):
        self.scan_thread.stop()
    
    def refresh_motor_tree(self):
        self.window.motor_tree.clear()
        
        for b in self.ids.keys():
            if not self.ids[b]:
                continue
            baud_root = PyQt4.QtGui.QTreeWidgetItem(self.window.motor_tree, [str(b)])
            baud_root.setExpanded(True)
        
            #baud_root.setFlags(PyQt4.QtCore.Qt.ItemFlags())
        
            dxl_lock.acquire()
            dxl_io = get_dxl_connection(self.get_port(), b)
        
            for mid, model in self.ids[b]:
                mid_root = PyQt4.QtGui.QTreeWidgetItem(baud_root, ['', str(mid), model])
                mid_root.setExpanded(True)
        
            dxl_lock.release()
    
    
    def get_port(self):
        return self.port
    
    def get_baudrates(self):
        baudrates = []
        
        for i in range(len(self.window.baud_checkboxes)):
            checkbox = self.window.baud_checkboxes.item(i)
            if checkbox.checkState() == 2:
                baudrates.append(int(checkbox.text()))
        
        return baudrates
    
    def get_baudrate_index(self, baudrate):
        return (1000000, 500000, 400000, 250000, 200000, 117647, 57142, 19230, 9615).index(baudrate)
    
    def get_status_return_level_index(self, level):
        return 2 - level
    
    def get_id_range(self):
        minimum = self.window.minimum_spinBox.value()
        maximum = self.window.maximum_spinBox.value()
        return range(minimum, maximum + 1)
    
    def motors_selected(self):
        if self.update_position_thread:
            self.update_position_thread.live = False
        
        items = self.window.motor_tree.selectedItems()
        items = filter(lambda item: item.parent(), items)
        
        if not items:
            return
    
        self.enable_motor_view()
    
        self.motors = {}
        for item in items:
            mid = int(item.text(1))
            b = int(item.parent().text(0))
            
            if not self.motors.has_key(b):
                self.motors[b] = []
            
            self.motors[b].append(mid)
    
        b = self.motors.keys()[0]
        mid = self.motors[b][0]
        port = self.get_port()
        
        eeprom = self.get_eeprom_values(port, b, mid)
        self.display_eeprom_values(eeprom)
        
        if len(items) == 1:
            limits = 180 if eeprom['model'].startswith('MX') else 150
            self.window.position_dial.setMinimum(-limits)
            self.window.position_dial.setMaximum(limits)
            self.window.goal_dial.setMinimum(-limits)
            self.window.goal_dial.setMaximum(limits)
            
            self.window.goal_dial.setValue(get_dxl_connection(port, b).get_current_position(mid))
            
            self.update_position_thread = UpdatePositionThread(port, b, mid, self.window.position_dial)
            self.update_position_thread.start()
    
        else:
            self.window.id_spinBox.setEnabled(False)
            self.window.position_label.setEnabled(False)
            self.window.goal_dial.setEnabled(False)

    
    def goal_position_changed(self, pos):
        b = self.motors.keys()[0]
        
        dxl_lock.acquire()
        dxl_io = get_dxl_connection(self.get_port(), b)
        if dxl_io.is_torque_enabled(self.motors[b][0]):
            self.window.torque_checkBox.setCheckState(2)
            dxl_io.set_goal_position(self.motors[b][0], pos)
        dxl_lock.release()


    def toggle_torque(self, state):
        dxl_lock.acquire()
        
        for b in self.motors.keys():
            dxl_io = get_dxl_connection(self.get_port(), b)
            
            for mid in self.motors[b]:
                if state == 2:
                    pos = dxl_io.get_current_position(mid)
                    dxl_io.set_goal_position(mid, pos)
                    dxl_io.enable_torque(mid)
                else:
                    dxl_io.disable_torque(mid)
        
        dxl_lock.release()
        
        if len(self.motors.keys()) == 1 and len(self.motors[self.motors.keys()[0]]) == 1:
            self.window.goal_dial.setValue(self.window.position_dial.value())

    def get_eeprom_values(self, port, b, mid):
        dxl_lock.acquire()
        
        dxl_io = get_dxl_connection(port, b)
        eeprom = {}
        
        eeprom['id'] = mid
        eeprom['baudrate'] = b
        eeprom['model'] = dxl_io.get_model(mid)
        eeprom['return_delay_time'] = dxl_io.get_return_delay_time(mid)
        eeprom['status_return_level'] = dxl_io.get_status_return_level(mid)
        eeprom['firmware_version'] = dxl_io.get_firmware_version(mid)
        eeprom['max_torque'] = dxl_io.get_max_torque(mid)
        eeprom['angle_limits'] = dxl_io.get_angle_limits(mid)
        eeprom['torque_enable'] = dxl_io.is_torque_enabled(mid)
        
        dxl_lock.release()
        return eeprom
    
    def display_eeprom_values(self, eeprom):
        if 'id' in eeprom:
            self.window.id_spinBox.setValue(eeprom['id'])
        
        self.window.baud_comboBox.setCurrentIndex(self.get_baudrate_index(eeprom['baudrate']))
        self.window.returndelaytime_horizontalSlider.setValue(eeprom['return_delay_time'])
        self.window.statusreturnlevel_comboBox.setCurrentIndex(self.get_status_return_level_index(eeprom['status_return_level']))
        if 'firmware_version' in eeprom:
            self.window.firmware_label.setText(str(eeprom['firmware_version']))
        self.window.torquemax_horizontalSlider.setValue(eeprom['max_torque'])
        
        limits = 180 if eeprom['model'].startswith('MX') else 150
        self.window.minimum_dial.setMinimum(-limits)
        self.window.minimum_dial.setMaximum(limits)
        self.window.minimum_dial.setValue(eeprom['angle_limits'][0])
        
        self.window.maximum_dial.setMinimum(-limits)
        self.window.maximum_dial.setMaximum(limits)
        self.window.maximum_dial.setValue(eeprom['angle_limits'][1])
        
        self.window.torque_checkBox.setCheckState(eeprom['torque_enable'] * 2)
    
    def reset_eeprom_values(self):
        default_eeprom = {
            'return_delay_time': 0,
            'status_return_level': 2,
            'max_torque': 100,
        }
        
        dxl_lock.acquire()
        for b in self.motors.keys():
            if b == 1000000:
                continue
            
            for mid in self.motors[b][:]:
                dxl_io = get_dxl_connection(self.get_port(), b)
                model = dxl_io.get_model(mid)
                
                dxl_io.set_baudrate(mid, 1000000)
                self.motors[b].remove(mid)
                if 1000000 not in self.motors:
                    self.motors[1000000] = []
                self.motors[1000000].append(mid)
                self.motors[1000000].sort()
            
                self.ids[b].remove((mid, model))
                if 1000000 not in self.ids:
                    self.ids[1000000] = []
                self.ids[1000000].append((mid, model))
                self.ids[1000000].sort()

        dxl_lock.release()
        
        for mid in self.motors[1000000]:
            eeprom = self.get_eeprom_values(self.get_port(), 1000000, mid)
            
            dxl_lock.acquire()
            dxl_io = get_dxl_connection(self.get_port(), 1000000)
            
            if eeprom['return_delay_time'] != default_eeprom['return_delay_time']:
                dxl_io.set_return_delay_time(mid, default_eeprom['return_delay_time'])
            
            if eeprom['status_return_level'] != default_eeprom['status_return_level']:
                dxl_io.set_status_return_level(mid, default_eeprom['status_return_level'])
            
            if eeprom['max_torque'] != default_eeprom['max_torque']:
                dxl_io.set_max_torque(mid, default_eeprom['max_torque'])
            
            model = dxl_io.get_model(mid)
            limits = 180 if eeprom['model'].startswith('MX') else 150
            if tuple(eeprom['angle_limits']) != (-limits, limits):
                dxl_io.set_angle_limits(mid, -limits, limits)
            
            dxl_lock.release()
        
        self.refresh_motor_tree()
    
    
    def update_eeprom(self):
        new_b = int(self.window.baud_comboBox.currentText())
        new_rdt = self.window.returndelaytime_horizontalSlider.value()
        new_srl = 2 - int(self.window.statusreturnlevel_comboBox.currentIndex())
        new_max_torque = self.window.torquemax_horizontalSlider.value()
        new_angle_limits = (self.window.minimum_dial.value(), self.window.maximum_dial.value())
        
        for b in self.motors.keys():
            for mid in self.motors[b]:
                eeprom = self.get_eeprom_values(self.get_port(), b, mid)
                
                dxl_lock.acquire()
                dxl_io = get_dxl_connection(self.get_port(), b)
                
                if eeprom['return_delay_time'] != new_rdt:
                    dxl_io.set_return_delay_time(mid, new_rdt)
                
                if eeprom['status_return_level'] != new_srl:
                    dxl_io.set_status_return_level(mid, new_srl)
                
                if eeprom['max_torque'] != new_max_torque:
                    dxl_io.set_max_torque(mid, new_max_torque)
                
                if tuple(map(int, eeprom['angle_limits'])) != new_angle_limits:
                    dxl_io.set_angle_limits(mid, new_angle_limits[0], new_angle_limits[1])
                
                dxl_lock.release()
        
        remove_list = []
        should_refresh = False
        for b in self.motors.keys():
            for mid in self.motors[b]:
                if b != new_b:
                    model = filter(lambda a: a[0] == mid, self.ids[b])[0][1]
                    self.ids[b].remove((mid, model))
                    
                    if not self.ids.has_key(new_b):
                        self.ids[new_b] = []
                    
                    self.ids[new_b].append((mid, model))
                    self.ids[new_b].sort()
                    should_refresh = True
                    
                    remove_list.append((b, mid, new_b))
                    
                    dxl_lock.acquire()
                    dxl_io = get_dxl_connection(self.get_port(), b)
                    dxl_io.set_baudrate(mid, new_b)
                    dxl_lock.release()
        
        for b, mid, new_b in remove_list:
            self.motors[b].remove(mid)
            if not self.motors.has_key(new_b):
                self.motors[new_b] = []
            self.motors[new_b].append(mid)
        
        if should_refresh:
            self.refresh_motor_tree()
        
        if len(self.motors.keys()) == 1 and len(self.motors[self.motors.keys()[0]]) == 1:
            new_id = self.window.id_spinBox.value()
            mid = self.motors.values()[0][0]
            
            all_ids = self.ids[self.motors.keys()[0]]
            if new_id in all_ids:
                pass
            else:
                self.update_position_thread.live = False
                self.update_position_thread = UpdatePositionThread(self.get_port(), self.motors.keys()[0], new_id, self.window.position_dial)
                
                dxl_lock.acquire()
                #get_dxl_connection(self.get_port(), self.motors.keys()[0]).change_id(mid, new_id)
                dxl_lock.release()
                
                self.update_position_thread.start()
    
    def enable_motor_view(self):
        for i in range(len(self.window.motor_gridLayout)):
            self.window.motor_gridLayout.itemAt(i).widget().setEnabled(True)
        self.window.position_dial.setEnabled(False)
    
    def disable_motor_view(self):
        for i in range(len(self.window.motor_gridLayout)):
            self.window.motor_gridLayout.itemAt(i).widget().setEnabled(False)


if __name__ == '__main__':
    app = HerboristApp(sys.argv)
    app.window.show()
    sys.exit(app.exec_())

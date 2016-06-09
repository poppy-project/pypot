import sys
import time
import itertools
import threading

import PyQt4.QtCore
import PyQt4.QtGui
import PyQt4.uic

from collections import defaultdict
from pkg_resources import resource_filename

import pypot.dynamixel


# MARK: - DxlIO connection

__dxl_io = None
__lock = threading.Lock()


def get_dxl_connection(port, baudrate, protocol="MX"):
    global __dxl_io

    __lock.acquire()
    if protocol == "XL":
        __dxl_io = pypot.dynamixel.Dxl320IO(port, baudrate, use_sync_read=False)
    else:
        __dxl_io = pypot.dynamixel.DxlIO(port, baudrate, use_sync_read=False)
    return __dxl_io


def release_dxl_connection():
    __dxl_io.close()
    __lock.release()


class HerboristApp(PyQt4.QtGui.QApplication):
    def __init__(self, argv):
        PyQt4.QtGui.QApplication.__init__(self, argv)
        self.window = PyQt4.uic.loadUi(resource_filename('pypot', '/tools/herborist/herborist.ui'))

        self.enable_motor_view(False)

        # slider / lcd connections
        self.window.rdt_slider.valueChanged.connect(self.window.rdt_lcd.display)
        self.window.torque_max_slider.valueChanged.connect(self.window.torque_max_lcd.display)
        self.window.lower_limit_dial.valueChanged.connect(self.window.lower_limit_lcd.display)
        self.window.upper_limit_dial.valueChanged.connect(self.window.upper_limit_lcd.display)
        self.window.present_position_dial.valueChanged.connect(self.window.present_position_lcd.display)
        self.window.goal_position_dial.valueChanged.connect(self.window.goal_position_lcd.display)

        # Connect the button to their cb
        self.window.scan_button.pressed.connect(self.start_scanning)
        self.window.abort_button.pressed.connect(self.abort_scanning)

        # We manually uncheck most baudrates in the selection list
        # as unchecking them in the ui editor make the checkbox goes away
        for i in range(1, len(self.window.baudrate_list)):
            self.window.baudrate_list.item(i).setCheckState(False)

        # We prevent the minimum id to be greater than the maximum id
        def min_id_changed(self, new_id):
            if new_id >= self.window.max_id.value():
                self.window.min_id.setValue(self.window.max_id.value())

        def max_id_changed(self, new_id):
            if new_id <= self.window.min_id.value():
                self.window.max_id.setValue(self.window.min_id.value())

        self.window.min_id.valueChanged.connect(lambda i: min_id_changed(self, i))
        self.window.max_id.valueChanged.connect(lambda i: max_id_changed(self, i))

        # We automatically refresh the port list
        self.refresh_port_thread = self.UpdatePortThread()
        self.refresh_port_thread.port_updated.connect(self.update_port)
        self.refresh_port_thread.start()

        # Motor View
        self.window.motor_tree.itemSelectionChanged.connect(self.update_motor_view)
        self.window.goal_position_dial.valueChanged.connect(self.update_motor_position)
        self.window.update_eeprom_button.pressed.connect(self.update_eeprom)
        self.window.torque_checkbox.stateChanged.connect(self.switch_torque)

        self.refresh_motor_thread = None

    # MARK: - Port update

    class UpdatePortThread(PyQt4.QtCore.QThread):
        port_updated = PyQt4.QtCore.pyqtSignal(list)

        def __init__(self):
            PyQt4.QtCore.QThread.__init__(self)
            self.daemon = True

        def run(self):
            while True:
                new_ports = pypot.dynamixel.get_available_ports()
                self.port_updated.emit(new_ports)
                time.sleep(0.1)

    def update_port(self, new_ports):
        old_ports = []
        for i in range(len(self.window.port_box)):
            old_ports.append(str(self.window.port_box.itemText(i)))

        selected_port = self.window.port_box.currentText()

        if old_ports != new_ports:
            self.window.port_box.clear()
            self.window.port_box.addItems(new_ports)

            for i in range(len(self.window.port_box)):
                if self.window.port_box.itemText(i) == selected_port:
                    self.window.port_box.setCurrentIndex(i)
                    break

            if old_ports and not new_ports:
                self.window.scan_button.setEnabled(False)
            elif not old_ports and new_ports:
                self.window.scan_button.setEnabled(True)

    # MARK: - Motor Scan
    def update_motor_tree(self, baud_for_ids):
        self.window.motor_tree.clear()

        for b, ids in baud_for_ids.iteritems():
            baud_root = PyQt4.QtGui.QTreeWidgetItem(self.window.motor_tree, [str(b)])
            baud_root.setExpanded(True)
            f = int(baud_root.flags()) - int(PyQt4.QtCore.Qt.ItemIsSelectable)
            baud_root.setFlags(PyQt4.QtCore.Qt.ItemFlags(f))

            dxl_io = get_dxl_connection(self.port, b, self.protocol)
            models = dxl_io.get_model(ids)
            release_dxl_connection()

            for id, model in zip(ids, models):
                PyQt4.QtGui.QTreeWidgetItem(baud_root, ['', str(id), model])

    def start_scanning(self):
        self.window.scan_button.setEnabled(False)
        self.window.motor_tree.setEnabled(False)
        self.window.abort_button.setEnabled(True)

        self.window.motor_tree.clear()

        baudrates = []
        for i in range(len(self.window.baudrate_list)):
            checkbox = self.window.baudrate_list.item(i)
            if checkbox.checkState() == 2:
                b = int(checkbox.text())
                if b == 57600 and self.usb_device == "USB2DYNAMIXEL":
                    b = 57142
                baudrates.append(b)

        id_range = range(self.window.min_id.value(), self.window.max_id.value() + 1)

        self.window.scan_progress.setValue(0)
        self.window.scan_progress.setMaximum(len(baudrates) * len(id_range) - 1)

        self.scan_thread = self.ScanThread(self.port, baudrates, self.protocol, id_range,
                                           self.window.motor_tree, self.window.scan_progress)
        self.scan_thread.done.connect(self.done_scanning)
        self.scan_thread.part_done.connect(self.window.scan_progress.setValue)
        self.scan_thread.start()

    def abort_scanning(self):
        self.scan_thread.abort()

    def done_scanning(self):
        self.window.motor_tree.setEnabled(True)
        self.window.abort_button.setEnabled(False)
        self.window.scan_button.setEnabled(True)

    class ScanThread(PyQt4.QtCore.QThread):
        done = PyQt4.QtCore.pyqtSignal()
        part_done = PyQt4.QtCore.pyqtSignal(int)

        def __init__(self, port, baudrates, protocol, id_range,
                     motor_tree, scan_progress):

            PyQt4.QtCore.QThread.__init__(self)
            self.daemon = True

            self.running = threading.Event()
            self.running.set()

            self.port = port
            self.baudrates = baudrates
            self.protocol = protocol
            self.id_range = id_range

            self.motor_tree = motor_tree
            self.scan_progress = scan_progress

        def run(self):
            for b in self.baudrates:
                baud_root = PyQt4.QtGui.QTreeWidgetItem(self.motor_tree, [str(b)])
                baud_root.setExpanded(True)
                f = int(baud_root.flags()) - int(PyQt4.QtCore.Qt.ItemIsSelectable)
                baud_root.setFlags(PyQt4.QtCore.Qt.ItemFlags(f))

                dxl_io = get_dxl_connection(self.port, b, self.protocol)

                for id in self.id_range:
                    if not self.running.is_set():
                        break

                    if dxl_io.ping(id):
                        model = dxl_io.get_model((id, ))[0]
                        PyQt4.QtGui.QTreeWidgetItem(baud_root, ['', str(id), model])

                    self.part_done.emit(self.scan_progress.value() + 1)

                release_dxl_connection()

            self.done.emit()

        def abort(self):
            self.scan_progress.setValue(0)
            self.running.clear()

    # MARK: - Motor View
    def update_motor_view(self):
        if self.refresh_motor_thread:
            self.refresh_motor_thread.stop()
            self.refresh_motor_thread.wait()

        if not self.selected_motors:
            self.enable_motor_view(False)
            return

        self.enable_motor_view(True)

        if len(list(itertools.chain(*self.selected_motors.values()))) > 1:
            for widget_name in ('id_spinbox',
                                'present_position_dial',
                                'goal_position_dial',
                                'present_position_lcd',
                                'goal_position_lcd'):
                getattr(self.window, widget_name).setEnabled(False)

        dxl_io = get_dxl_connection(self.port, self.baudrate, self.protocol)
        srl = dxl_io.get_status_return_level((self.id, ), convert=False)[0]
        if srl != 0:
            model = dxl_io.get_model((self.id, ))[0]
            rdt = dxl_io.get_return_delay_time((self.id, ))[0]
            firmware = dxl_io.get_firmware((self.id, ))[0]
            torque_max = dxl_io.get_max_torque((self.id, ))[0]
            angle_limit = dxl_io.get_angle_limit((self.id, ))[0]
            goal_pos = dxl_io.get_goal_position((self.id, ))[0]
            torque_enable = dxl_io.is_torque_enabled((self.id, ))[0]
        release_dxl_connection()

        self.window.id_spinbox.setValue(self.id)

        for i in range(len(self.window.baud_combobox)):
            if int(self.window.baud_combobox.itemText(i)) == self.baudrate:
                self.window.baud_combobox.setCurrentIndex(i)
                break

        self.window.srl_combobox.setCurrentIndex(srl)

        if srl != 0:
            self.window.rdt_slider.setValue(rdt)
            self.window.firmware_label.setText(str(firmware))
            self.window.torque_max_slider.setValue(torque_max)

            limit = 180 if model.startswith('MX') else 150
            for widget_name in ('lower_limit_dial', 'upper_limit_dial',
                                'present_position_dial', 'goal_position_dial'):
                getattr(self.window, widget_name).setMinimum(-limit)
                getattr(self.window, widget_name).setMaximum(limit)

            self.window.lower_limit_dial.setValue(angle_limit[0])
            self.window.upper_limit_dial.setValue(angle_limit[1])
            self.window.goal_position_dial.setValue(goal_pos)
            self.window.torque_checkbox.setChecked(torque_enable)

        self.refresh_motor_thread = self.UpdateMotorThread(self.port, self.baudrate, self.protocol, self.id)
        self.refresh_motor_thread.position_updated.connect(self.motor_position_updated)
        self.refresh_motor_thread.start()

    def update_motor_position(self, pos):
        if self.window.torque_checkbox.checkState():
            dxl_io = get_dxl_connection(self.port, self.baudrate, self.protocol)
            dxl_io.set_goal_position({self.id: pos})
            time.sleep(0.05)
            release_dxl_connection()

    def motor_position_updated(self, pos):
        self.window.present_position_dial.setValue(pos)

    def switch_torque(self, torque_enable):
        if torque_enable:
            self.window.goal_position_dial.setEnabled(True)
            self.window.goal_position_lcd.setEnabled(True)
        else:
            self.window.goal_position_dial.setEnabled(False)
            self.window.goal_position_lcd.setEnabled(False)

        for b, ids in self.selected_motors.iteritems():
            dxl_io = get_dxl_connection(self.port, b, self.protocol)
            (dxl_io.enable_torque if torque_enable else dxl_io.disable_torque)(ids)
            time.sleep(0.05)
            release_dxl_connection()

    def enable_motor_view(self, enabled):
        for i in range(len(self.window.motor_layout)):
            self.window.motor_layout.itemAt(i).widget().setEnabled(enabled)

    def update_eeprom(self):
        if self.refresh_motor_thread:
            self.refresh_motor_thread.stop()
            self.refresh_motor_thread.wait()

        rdt = self.window.rdt_slider.value()
        srl = self.window.srl_combobox.currentIndex()
        torque_max = self.window.torque_max_slider.value()
        lower_limit = self.window.lower_limit_dial.value()
        upper_limit = self.window.upper_limit_dial.value()
        new_id = self.window.id_spinbox.value()

        for b, ids in self.selected_motors.iteritems():
            dxl_io = get_dxl_connection(self.port, b, self.protocol)
            dxl_io.set_return_delay_time(dict(zip(ids, itertools.repeat(rdt))))
            dxl_io.set_status_return_level(dict(zip(ids, itertools.repeat(srl))), convert=False)
            dxl_io.set_max_torque(dict(zip(ids, itertools.repeat(torque_max))))
            dxl_io.set_angle_limit(dict(zip(ids, itertools.repeat((lower_limit, upper_limit)))))
            time.sleep(0.15)
            release_dxl_connection()

        new_ids = self.ids.copy()

        old_ids = self.selected_motors.values()
        if len(old_ids) == 1 and len(old_ids[0]) == 1 and new_id != old_ids[0][0]:
            b, old_id = self.selected_motors.keys()[0], old_ids[0][0]
            dxl_io = get_dxl_connection(self.port, b, self.protocol)
            try:
                dxl_io.change_id({old_id: new_id})

                l = new_ids[b]
                l[l.index(old_id)] = new_id
                new_ids[b] = l

            except ValueError:
                PyQt4.QtGui.QMessageBox.about(self.window,
                                              '',
                                              'This id is already used.')
                pass

            release_dxl_connection()

        for b, ids in self.selected_motors.iteritems():
            new_b = int(self.window.baud_combobox.currentText())
            if b != new_b:
                dxl_io = get_dxl_connection(self.port, b, self.protocol)
                dxl_io.change_baudrate(dict(zip(ids, itertools.repeat(new_b))))
                time.sleep(0.1)
                release_dxl_connection()

            for id in ids:
                new_ids[new_b].append(id)
                new_ids[b].remove(id)
                new_ids[new_b].sort()

        self.update_motor_tree(new_ids)

    class UpdateMotorThread(PyQt4.QtCore.QThread):
        position_updated = PyQt4.QtCore.pyqtSignal(int)

        def __init__(self, port, baudrate, protocol, mid):
            PyQt4.QtCore.QThread.__init__(self)
            self.running = threading.Event()
            self.running.set()

            self.port = port
            self.baudrate = baudrate
            self.protocol = protocol
            self.mid = mid

        def stop(self):
            self.running.clear()

        def run(self):
            while self.running.is_set():
                dxl_io = get_dxl_connection(self.port, self.baudrate, self.protocol)
                pos = dxl_io.get_present_position((self.mid, ))[0]
                release_dxl_connection()

                self.position_updated.emit(pos)

                time.sleep(0.05)

    # MARK: - Shortcut properties
    @property
    def port(self):
        return str(self.window.port_box.currentText())

    @property
    def protocol(self):
        return str(self.window.protocol_box.currentText())

    @property
    def usb_device(self):
        return str(self.window.usb_device_box.currentText())

    @property
    def baudrate(self):
        return self.selected_motors.keys()[0]

    @property
    def id(self):
        return self.selected_motors[self.baudrate][0]

    @property
    def selected_motors(self):
        motors = defaultdict(list)

        selected_items = self.window.motor_tree.selectedItems()
        selected_items = [item for item in selected_items if item.parent()]

        for item in selected_items:
            motors[int(item.parent().text(0))].append(int(item.text(1)))

        return motors

    @property
    def ids(self):
        ids = defaultdict(list)

        root = self.window.motor_tree.invisibleRootItem()
        for i in range(root.childCount()):
            baud_node = root.child(i)

            if baud_node.text(0):
                b = int(baud_node.text(0))
                ids[b]
            else:
                ids[0].append(int(baud_node.text(1)))

            for j in range(baud_node.childCount()):
                id_node = baud_node.child(j)
                ids[b].append(int(id_node.text(1)))

        return ids


def main():
    app = HerboristApp(sys.argv)
    app.window.show()
    sys.exit(app.exec_())

    __lock.acquire()

if __name__ == '__main__':
    main()

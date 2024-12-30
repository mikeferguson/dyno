#!/usr/bin/env python3

# Copyright 2019-2024 Michael Ferguson
# All Rights Reserved

"""
Dyno Interface
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

import argparse
import time
from math import sin, cos

from dyno import DynoBoardInterface, RoadLoad

class DynoGUI:

    def __init__(self, load_interface=None, ros2_interface=None):
        self.reset()

        # Plots
        self.torque = pg.PlotWidget(title="Torque")
        self.speed = pg.PlotWidget(title="Speed")
        self.power = pg.PlotWidget(title="Power")

        # Status / Controls
        self.status_label = QtWidgets.QLabel(text="<b>Measurements</b>")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.status_label.setMargin(10)
        self.torque_value = QtWidgets.QLabel(text="0.0")
        self.torque_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.speed_value = QtWidgets.QLabel(text="0.0")
        self.speed_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.voltage_value = QtWidgets.QLabel(text="0.0")
        self.voltage_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.current_value = QtWidgets.QLabel(text="0.0")
        self.current_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Absorber controls
        self.absorber_label = QtWidgets.QLabel(text="<b>Absorber Control</b>")
        self.absorber_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.absorber_label.setMargin(10)
        # Selection of absorber mode
        self.absorber_disable = QtWidgets.QRadioButton("Disabled")
        self.absorber_disable.setChecked(True)
        self.absorber_manual_speed = QtWidgets.QRadioButton("Speed Mode")
        self.absorber_road_load = QtWidgets.QRadioButton("Road Load Mode")
        # Absorber speed mode options
        self.absorber_desired_speed = QtWidgets.QDoubleSpinBox()
        self.absorber_desired_speed.setRange(0.0, 1000.0)
        self.absorber_desired_speed.setSingleStep(0.5)
        # Absorber road load options
        self.absorber_road_load_j = QtWidgets.QDoubleSpinBox()
        self.absorber_road_load_j.setRange(0.0, 1000.0)
        self.absorber_road_load_j.setSingleStep(0.5)
        self.absorber_road_load_c0 = QtWidgets.QDoubleSpinBox()
        self.absorber_road_load_c0.setRange(0.0, 1000.0)
        self.absorber_road_load_c0.setSingleStep(0.5)
        self.absorber_road_load_c1 = QtWidgets.QDoubleSpinBox()
        self.absorber_road_load_c1.setRange(0.0, 1000.0)
        self.absorber_road_load_c1.setSingleStep(0.5)

        self.buck_label = QtWidgets.QLabel(text="<b>Input Power Control</b>")
        self.buck_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.buck_label.setMargin(10)
        self.buck_voltage = QtWidgets.QDoubleSpinBox()
        self.buck_voltage.setRange(0.0, 48.0)
        self.buck_voltage.setSingleStep(1.0)
        self.buck_current = QtWidgets.QDoubleSpinBox()
        self.buck_current.setRange(0.0, 5.0)
        self.buck_current.setSingleStep(0.25)

        self.do_capture = False
        self.capture_button = QtWidgets.QPushButton("Start")
        self.capture_button.clicked.connect(self.triggerCapture)
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.clear_button.clicked.connect(self.reset)

        # Layout
        self.controls = QtWidgets.QWidget()
        self.controls.setFixedWidth(200)
        self.controls_layout = QtWidgets.QVBoxLayout()
        self.controls.setLayout(self.controls_layout)

        self.controls_layout.addWidget(self.status_label)
        self.status_layout = QtWidgets.QGridLayout()
        self.status_layout.addWidget(QtWidgets.QLabel(text="Torque (Nm)"), 0, 0)
        self.status_layout.addWidget(self.torque_value, 0, 1)
        self.status_layout.addWidget(QtWidgets.QLabel(text="Speed (rad/s)"), 1, 0)
        self.status_layout.addWidget(self.speed_value, 1, 1)
        self.status_layout.addWidget(QtWidgets.QLabel(text="Input Voltage (V)"), 2, 0)
        self.status_layout.addWidget(self.voltage_value, 2, 1)
        self.status_layout.addWidget(QtWidgets.QLabel(text="Input Current (A)"), 3, 0)
        self.status_layout.addWidget(self.current_value, 3, 1)
        self.controls_layout.addLayout(self.status_layout)

        self.controls_layout.addWidget(self.absorber_label)
        self.controls_layout.addWidget(self.absorber_disable)
        self.controls_layout.addWidget(self.absorber_manual_speed)
        self.absorber_speed_layout = QtWidgets.QGridLayout()
        self.absorber_speed_layout.addWidget(QtWidgets.QLabel("Speed (rad/s)"), 0, 0)
        self.absorber_speed_layout.addWidget(self.absorber_desired_speed, 0, 1)
        self.controls_layout.addLayout(self.absorber_speed_layout)
        self.controls_layout.addWidget(self.absorber_road_load)
        self.absorber_road_load_layout = QtWidgets.QGridLayout()
        self.absorber_road_load_layout.addWidget(QtWidgets.QLabel("J"), 0, 0)
        self.absorber_road_load_layout.addWidget(self.absorber_road_load_j, 0, 1)
        self.absorber_road_load_layout.addWidget(QtWidgets.QLabel("C0"), 1, 0)
        self.absorber_road_load_layout.addWidget(self.absorber_road_load_c0, 1, 1)
        self.absorber_road_load_layout.addWidget(QtWidgets.QLabel("C1"), 2, 0)
        self.absorber_road_load_layout.addWidget(self.absorber_road_load_c1, 2, 1)
        self.controls_layout.addLayout(self.absorber_road_load_layout)

        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.capture_button)
        self.controls_layout.addWidget(self.clear_button)

        self.layout = QtWidgets.QGridLayout()
        self.window = QtWidgets.QWidget()
        self.window.setLayout(self.layout)
        self.layout.addWidget(self.controls, 0, 0, 3, 1)
        self.layout.addWidget(self.torque, 0, 1, 1, 2)
        self.layout.addWidget(self.speed, 1, 1, 1, 2)
        self.layout.addWidget(self.power, 2, 1, 1, 2)

        self.window.setWindowTitle("Dyno Control GUI")
        self.window.show()

        self.dyno = DynoBoardInterface()
        self.road_load = RoadLoad(self.dyno, 0, 0, 0)
        self.absorber = load_interface
        if self.absorber is None:
            print("No absorber load, disabling")
            self.absorber_disable.setEnabled(False)
            self.absorber_manual_speed.setEnabled(False)
            self.absorber_desired_speed.setEnabled(False)
            self.absorber_road_load.setEnabled(False)
            self.absorber_road_load_j.setEnabled(False)
            self.absorber_road_load_c0.setEnabled(False)
            self.absorber_road_load_c1.setEnabled(False)

        self.ros2 = ros2_interface
        if self.ros2:
            self.ros2.gui = self

    ## @brief Reset data
    def reset(self):
        self.start = 0.0
        self.time_stamps = []
        self.input_voltage = []
        self.input_current = []
        self.input_power = []
        self.output_torque = []
        self.output_speed = []
        self.absorber_speed = []
        self.start_time = time.time()

    ## @brief Start capture
    def start_capture(self):
        self.do_capture = True
        self.capture_button.setText("Stop")
        self.reset()

    ## @brief Stop capture
    def stop_capture(self):
        self.do_capture = False
        self.capture_button.setText("Start")
        self.road_load.reset()

    ## @brief Start/stop capture
    def triggerCapture(self):
        if self.do_capture:
            self.stop_capture()
        else:
            self.start_capture()

    ## @brief Sample data from dyno
    def sample(self):
        if not self.do_capture:
            return

        data = self.dyno.update()
        if data is None:
            # No data yet to process
            return

        if not self.time_stamps:
            self.start = data[0]
        stamp = (data[0] - self.start) / 25000.0
        self.time_stamps.append(stamp)
        # system_voltage = data[1]
        self.input_voltage.append(data[2])
        self.input_current.append(data[3])
        self.output_torque.append(data[4])
        # position = data[5]
        self.output_speed.append(data[6] / 8)  # TODO: update firmware after changing encoder
        self.input_power.append(data[2] * data[3])

        # Do absorber control
        if self.absorber_road_load.isChecked():
            self.road_load.j = self.absorber_road_load_j.value()
            self.road_load.c0 = self.absorber_road_load_c0.value()
            self.road_load.c1 = self.absorber_road_load_c1.value()
            self.absorber.set_radians_per_sec(self.road_load.getVelocityCommand())
        elif self.absorber_manual_speed.isChecked():
            self.absorber.set_radians_per_sec(int(self.absorber_desired_speed.value()))

        self.absorber_speed.append(self.road_load.velocity)
        if self.ros2:
            self.ros2.publish(stamp, data[1], data[2], data[3], data[4], data[5], data[6] / 8)

    ## @brief Refresh the view
    def refresh(self):
        times = self.time_stamps[-1000:-1]
        torques = self.output_torque[-1000:-1]
        speeds = self.output_speed[-1000:-1]
        absorber_speeds = self.absorber_speed[-1000:-1]
        ePowers = self.input_power[-1000:-1]
        mPowers = [t*s for t, s in zip(torques, speeds)]

        try:
            self.torque_value.setText("%.3f" % self.output_torque[-1])
            self.speed_value.setText("%.3f" % self.output_speed[-1])
            self.voltage_value.setText("%.3f" % self.input_voltage[-1])
            self.current_value.setText("%.3f" % self.input_current[-1])
        except IndexError:
            # No data yet to show
            pass

        self.torque.plot(times, torques, clear=True)
        self.speed.plot(times, speeds, clear=True)
        yellow_pen = QtGui.QColor(255, 255, 0)
        if self.absorber_road_load.isChecked():
            self.speed.plot(times, absorber_speeds, pen=yellow_pen)
        self.power.plot(times, mPowers, clear=True)
        self.power.plot(times, ePowers, pen=yellow_pen)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vesc", help="Use VESC for absorber load interface", action="store_true")
    parser.add_argument("--ros", help="Enable ROS 2 interface", action="store_true")
    args, unknown = parser.parse_known_args()

    app = QtWidgets.QApplication([])

    absorber = None
    if args.vesc:
        from load_vesc import LoadVescInterface
        absorber = LoadVescInterface()

    ros2_interface = None
    if args.ros:
        from ros import DynoROS2
        ros2_interface = DynoROS2()

    gui = DynoGUI(absorber, ros2_interface)

    # Start sampling timer at 200hz
    sample = QtCore.QTimer()
    sample.timeout.connect(gui.sample)
    sample.start(5)

    # Start refresh timer at 10hz
    plot = QtCore.QTimer()
    plot.timeout.connect(gui.refresh)
    plot.start(100)

    app.exec_()

    if ros2_interface:
        ros2_interface.shutdown()

#!/usr/bin/env python3

# Copyright 2019-2025 Michael Ferguson
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
from load_powder_brake import LoadPowderBrake

class DynoGUI:

    # How fast to get updates from Dyno
    UPDATE_FREQUENCY = 200

    def __init__(self, load_interface=None, ros2_interface=None):
        self.reset()

        # Calibrated offsets
        self.offset_torque = 0.0
        self.offset_current = 0.0

        # Plots
        self.torque = pg.PlotWidget(title="Torque")
        self.torque.setMouseEnabled(x=False, y=False)
        self.speed = pg.PlotWidget(title="Speed")
        self.speed.setMouseEnabled(x=False, y=False)
        self.power = pg.PlotWidget(title="Power")
        self.power.setMouseEnabled(x=False, y=False)

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
        self.absorber_disable.toggled.connect(self.absorber_disable_callback)
        self.absorber_manual_torque = QtWidgets.QRadioButton("Torque Mode")
        # Absorber speed mode options
        self.absorber_desired_torque = QtWidgets.QDoubleSpinBox()
        self.absorber_desired_torque.setRange(0.0, 25.0)
        self.absorber_desired_torque.setSingleStep(0.1)

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
        self.zero_button = QtWidgets.QPushButton("Zero")
        self.zero_button.clicked.connect(self.zero)
        self.zero_button.setEnabled(False)

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
        self.controls_layout.addWidget(self.absorber_manual_torque)
        self.absorber_torque_layout = QtWidgets.QGridLayout()
        self.absorber_torque_layout.addWidget(QtWidgets.QLabel("Torque (Nm)"), 0, 0)
        self.absorber_torque_layout.addWidget(self.absorber_desired_torque, 0, 1)
        self.controls_layout.addLayout(self.absorber_torque_layout)

        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.capture_button)
        self.controls_layout.addWidget(self.clear_button)
        self.controls_layout.addWidget(self.zero_button)

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
        self.absorber = load_interface
        if self.absorber is None:
            print("No absorber load, disabling")
            self.absorber_disable.setEnabled(False)
            self.absorber_manual_torque.setEnabled(False)
            self.absorber_desired_torque.setEnabled(False)

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
        self.start_time = time.time()

    ## @brief Zero the offsets
    def zero(self):
        if len(self.input_current) <= 100:
            print("Cannot calibrate zeros - not enough data")
            return

        currents = self.input_current[-100:-1]
        offset = sum(currents) / len(currents)
        self.offset_current -= offset

        torques = self.output_torque[-100:-1]
        offset = sum(torques) / len(torques)
        self.offset_torque -= offset

    ## @brief Start capture
    def start_capture(self):
        self.do_capture = True
        self.capture_button.setText("Stop")
        self.zero_button.setEnabled(True)
        self.reset()

    ## @brief Stop capture
    def stop_capture(self):
        self.do_capture = False
        self.capture_button.setText("Start")
        self.zero_button.setEnabled(False)

    ## @brief Start/stop capture
    def triggerCapture(self):
        if self.do_capture:
            self.stop_capture()
        else:
            self.start_capture()

    ## @brief Send disable command
    def absorber_disable_callback(self):
        if self.absorber_disable.isChecked():
            self.absorber.set_torque(0.0)
            command = self.absorber.get_command()
            self.dyno.update(command_addon=command)

    ## @brief Sample data from dyno
    def sample(self):
        if not self.do_capture:
            return

        command = None
        if self.absorber_manual_torque.isChecked():
            self.absorber.set_torque(self.absorber_desired_torque.value())
            command = self.absorber.get_command()

        data = self.dyno.update(command_addon=command)
        if data is None:
            # No data yet to process
            return

        if not self.time_stamps:
            self.start = data[0]
        stamp = (data[0] - self.start) / 25000.0
        self.time_stamps.append(stamp)

        # Convert to named values
        # system_voltage = data[1]
        voltage = data[2]
        current = data[3] + self.offset_current
        torque = data[4] + self.offset_torque
        position = data[5]
        speed = data[6]
        self.input_voltage.append(voltage)
        self.input_current.append(current)
        self.output_torque.append(torque)
        self.output_speed.append(speed)
        self.input_power.append(voltage * current)

        if self.ros2:
            self.ros2.publish(stamp, data[1], voltage, current, torque, position, speed)

    ## @brief Refresh the view
    def refresh(self):
        # Display 10 seconds worth of data
        depth = 10 * self.UPDATE_FREQUENCY
        times = self.time_stamps[-depth:-1]
        torques = self.output_torque[-depth:-1]
        speeds = self.output_speed[-depth:-1]
        ePowers = self.input_power[-depth:-1]
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
        self.power.plot(times, mPowers, clear=True)
        yellow_pen = QtGui.QColor(255, 255, 0)
        self.power.plot(times, ePowers, pen=yellow_pen)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ros", help="Enable ROS 2 interface", action="store_true")
    args, unknown = parser.parse_known_args()

    app = QtWidgets.QApplication([])

    absorber = LoadPowderBrake()
    ros2_interface = None
    if args.ros:
        from ros import DynoROS2
        ros2_interface = DynoROS2()

    gui = DynoGUI(absorber, ros2_interface)

    # Start sampling timer
    sample = QtCore.QTimer()
    sample.timeout.connect(gui.sample)
    sample.start(int(1000 / gui.UPDATE_FREQUENCY))

    # Start refresh timer at 10hz
    plot = QtCore.QTimer()
    plot.timeout.connect(gui.refresh)
    plot.start(100)

    app.exec_()

    if ros2_interface:
        ros2_interface.shutdown()

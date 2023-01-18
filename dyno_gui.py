#!/usr/bin/env python3

# Copyright 2019-2023 Michael Ferguson
# All Rights Reserved

from PyQt5 import QtCore, QtGui
import pyqtgraph as pg

import time
from math import sin, cos

from dyno import DynoBoardInterface

class DynoGUI:

    def __init__(self):
        self.reset()

        # Plots
        self.torque = pg.PlotWidget(title="Torque")
        self.speed = pg.PlotWidget(title="Speed")
        self.power = pg.PlotWidget(title="Power")

        # Status / Controls
        self.status_label = QtGui.QLabel(text="<b>Measurements</b>")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.status_label.setMargin(10)
        self.torque_value = QtGui.QLabel(text="0.0")
        self.torque_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.speed_value = QtGui.QLabel(text="0.0")
        self.speed_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.voltage_value = QtGui.QLabel(text="0.0")
        self.voltage_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.current_value = QtGui.QLabel(text="0.0")
        self.current_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.absorber_label = QtGui.QLabel(text="<b>Absorber Control</b>")
        self.absorber_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.absorber_label.setMargin(10)
        self.absorber_disable = QtGui.QRadioButton("Disabled")
        self.absorber_disable.setChecked(True)
        self.absorber_disable.toggled.connect(self.absorberDisable)
        self.absorber_manual_speed = QtGui.QRadioButton("Speed Mode")
        self.absorber_manual_speed.toggled.connect(self.absorberSpeed)
        self.absorber_speed = QtGui.QDoubleSpinBox()
        self.absorber_speed.setRange(0.0, 1000.0)
        self.absorber_speed.setSingleStep(0.5)
        self.absorber_speed.setEnabled(False)

        self.buck_label = QtGui.QLabel(text="<b>Input Power Control</b>")
        self.buck_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.buck_label.setMargin(10)
        self.buck_voltage = QtGui.QDoubleSpinBox()
        self.buck_voltage.setRange(0.0, 48.0)
        self.buck_voltage.setSingleStep(1.0)
        self.buck_current = QtGui.QDoubleSpinBox()
        self.buck_current.setRange(0.0, 5.0)
        self.buck_current.setSingleStep(0.25)

        self.do_capture = False
        self.capture_button = QtGui.QPushButton("Start")
        self.capture_button.clicked.connect(self.triggerCapture)
        self.clear_button = QtGui.QPushButton("Clear")
        self.clear_button.clicked.connect(self.reset)

        # Layout
        self.controls = QtGui.QWidget()
        self.controls.setFixedWidth(200)
        self.controls_layout = QtGui.QVBoxLayout()
        self.controls.setLayout(self.controls_layout)

        self.controls_layout.addWidget(self.status_label)
        self.status_layout = QtGui.QGridLayout()
        self.status_layout.addWidget(QtGui.QLabel(text="Torque (Nm)"), 0, 0)
        self.status_layout.addWidget(self.torque_value, 0, 1)
        self.status_layout.addWidget(QtGui.QLabel(text="Speed (rad/s)"), 1, 0)
        self.status_layout.addWidget(self.speed_value, 1, 1)
        self.status_layout.addWidget(QtGui.QLabel(text="Input Voltage (V)"), 2, 0)
        self.status_layout.addWidget(self.voltage_value, 2, 1)
        self.status_layout.addWidget(QtGui.QLabel(text="Input Current (A)"), 3, 0)
        self.status_layout.addWidget(self.current_value, 3, 1)
        self.controls_layout.addLayout(self.status_layout)

        self.controls_layout.addWidget(self.absorber_label)
        self.controls_layout.addWidget(self.absorber_disable)
        self.controls_layout.addWidget(self.absorber_manual_speed)
        self.absorber_speed_layout = QtGui.QGridLayout()
        self.absorber_speed_layout.addWidget(QtGui.QLabel("Speed (rad/s)"), 0, 0)
        self.absorber_speed_layout.addWidget(self.absorber_speed, 0, 1)
        self.controls_layout.addLayout(self.absorber_speed_layout)

        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.capture_button)
        self.controls_layout.addWidget(self.clear_button)

        self.layout = QtGui.QGridLayout()
        self.window = QtGui.QWidget()
        self.window.setLayout(self.layout)
        self.layout.addWidget(self.controls, 0, 0, 3, 1)
        self.layout.addWidget(self.torque, 0, 1, 1, 2)
        self.layout.addWidget(self.speed, 1, 1, 1, 2)
        self.layout.addWidget(self.power, 2, 1, 1, 2)

        self.window.setWindowTitle("Dyno Control GUI")
        self.window.show()

        self.dyno = DynoBoardInterface()

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

    ## @brief Switch absorber modes
    def absorberDisable(self):
        self.absorber_speed.setEnabled(False)

    ## @brief Switch absorber modes
    def absorberSpeed(self):
        self.absorber_speed.setEnabled(True)

    ## @brief Start/stop capture
    def triggerCapture(self):
        if self.do_capture:
            self.do_capture = False
            self.capture_button.setText("Start")
        else:
            self.do_capture = True
            self.capture_button.setText("Stop")
            self.reset()

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
        self.time_stamps.append((data[0] - self.start) / 25000.0)
        # system_voltage = data[1]
        self.input_voltage.append(data[2])
        self.input_current.append(data[3])
        self.output_torque.append(data[4])
        # position = data[5]
        self.output_speed.append(data[6])
        if data[6] != 0.0:
            print(data[6])
        self.input_power.append(data[2] * data[3])

    ## @brief Refresh the view
    def refresh(self):
        times = self.time_stamps[-1000:-1]
        torques = self.output_torque[-1000:-1]
        speeds = self.output_speed[-1000:-1]
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
        self.power.plot(times, mPowers, clear=True)
        self.power.plot(times, ePowers, pen={"color": "FFFF00"})

if __name__ == "__main__":
    app = QtGui.QApplication([])

    gui = DynoGUI()

    # Start sampling timer at 200hz
    sample = QtCore.QTimer()
    sample.timeout.connect(gui.sample)
    sample.start(5)

    # Start refresh timer at 10hz
    plot = QtCore.QTimer()
    plot.timeout.connect(gui.refresh)
    plot.start(100)

    app.exec_()

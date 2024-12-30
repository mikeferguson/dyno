#!/usr/bin/env python3

# Copyright 2023-2024 Michael Ferguson
# All Rights Reserved

# https://github.com/LiamBindle/PyVESC
from pyvesc import VESC
from math import pi

class LoadVescInterface:

    # Motor has 14 pole pairs - 7 poles
    motor_poles = 7

    # Torque constant
    # Kt = 60 / (2 * pi * Kv) = 60 / (2 * pi * 149)
    kt = 0.064

    def __init__(self, port="/dev/ttyACM0"):
        self.vesc = VESC(serial_port=port, start_heartbeat=False)

    def set_duty_cycle(self, duty_cycle):
        self.vesc.set_duty_cycle(duty_cycle)

    def set_radians_per_sec(self, rads_sec):
        rpm = int(60.0 * rads_sec / (2 * pi) * self.motor_poles)
        self.vesc.set_rpm(rpm)

    def set_torque(self, torque):
        milliamps = int((torque / self.kt) * 1000.0)
        if abs(torque) < 0.2:
            milliamps = 0
        self.vesc.set_current(milliamps)


# this is just testing stuff
if __name__ == "__main__":
    import time
    l = LoadVescInterface()
    while True:
        l.set_radians_per_sec(25.0)
        time.sleep(0.01)

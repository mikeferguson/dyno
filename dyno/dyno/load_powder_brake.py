# Copyright 2025 Michael Ferguson
# All Rights Reserved

from dyno import getAnalogCommand

# Powder brake uses the analog DUT interface
class LoadPowderBrake:

    def __init__(self):
        self.torque = 0.0
        self.voltage = 0.0

    def set_torque(self, torque):
        # Store torque
        self.torque = torque
        # Convert torque to voltage
        if torque < 0.01:
            self.voltage = 0
        elif torque < 0.4:
            self.voltage = 0.75 * torque
        elif torque < 5.0:
            self.voltage = 0.259 + (0.161 * torque) - (0.0106 * torque * torque)
        else:
            self.voltage = 0.32 + (0.102 * torque) - (0.00125 * torque * torque)

    def get_torque(self):
        return self.torque

    def get_command(self):
        return getAnalogCommand(self.voltage)

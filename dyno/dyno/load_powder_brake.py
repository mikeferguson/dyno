# Copyright 2025 Michael Ferguson
# All Rights Reserved

from dyno import getAnalogCommand

# Powder brake uses the analog DUT interface
class LoadPowderBrake:

    # Volts per Nm - 10v = 50Nm
    # TODO: we need an isolated opamp to boost the 5v output to 10v, then rescale this
    scale = 10 / 50.0

    def __init__(self):
        self.voltage = 0.0

    def set_torque(self, torque):
        # Convert torque to voltage
        self.voltage = torque * self.scale

    def get_command(self):
        return getAnalogCommand(self.voltage)

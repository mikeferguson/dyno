import time
import numpy as np
import matplotlib.pyplot as plt

from dyno.dut.ros import DynoInterface

"""
Easy way to generate an efficiency map
"""
class EfficiencyMap:

    def __init__(self, vel_min, vel_max, vel_step, torque_min, torque_max, torque_step, motor, interface=None):
        self.velocity = np.arange(vel_min, vel_max + vel_step, vel_step)
        self.torque = np.arange(torque_min, torque_max + torque_step, torque_step).reshape(-1, 1)
        self.efficiency = (self.velocity * self.torque)
        self.motor = motor
        self.interface = interface or DynoInterface()
        self.clear()

    def clear(self):
        # Clear out all the efficiency measurements
        self.efficiency *= np.nan

    def add_sample(self, msg):
        # Actual measurements
        torque = abs(msg.torque)
        velocity = abs(msg.velocity)
        output_power = torque * velocity
        input_power = msg.buck_voltage * msg.buck_current
        efficiency = output_power / input_power
        # Figure out best index
        t = np.abs(self.torque - torque).argmin()
        v = np.abs(self.velocity - velocity).argmin()
        self.efficiency[t][v] = efficiency

    def run(self):
        for v in self.velocity:
            print("Setting motor velocity to %f" % v)
            for t in self.torque:
                print("Setting torque to %f" % t)
                self.motor.set_velocity(float(v), float(t))
                self.interface.set_load_torque(t)
                # TODO: properly wait for torque/velocity to settle
                time.sleep(2)
                self.add_sample(self.interface.get_data())

    def shutdown(self):
        self.interface.set_load_torque(0.0)
        self.interface.shutdown()

    def plot(self, title=None):
        title = title or 'Motor Efficiency'

        fig, ax = plt.subplots()
        fig.suptitle(title)
        X, Y = np.meshgrid(self.velocity, self.torque)
        cmap = plt.cm.plasma
        img = ax.contourf(X, Y, self.efficiency, cmap=cmap)
        ax.set_ylabel('Torque (Nm)')
        ax.set_xlabel('Velocity (rad/s)')
        cbar = fig.colorbar(img, ax=ax, extend='both')
        plt.show()

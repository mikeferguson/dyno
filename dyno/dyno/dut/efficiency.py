import time
import sys
import numpy as np
import matplotlib.pyplot as plt

from dyno.dut.ros import DynoInterface

"""
Easy way to generate an efficiency map
"""
class EfficiencyMap:

    def __init__(self, logfile=None):
        self.interface = None
        self.logfile = None
        if logfile:
            self.logfile = open(logfile, 'w')

    def configure(self, vel_min, vel_max, vel_step, torque_min, torque_max, torque_step, motor, interface=None):
        self.velocity = np.arange(vel_min, vel_max + vel_step, vel_step)
        self.torque = np.arange(torque_min, torque_max + torque_step, torque_step).reshape(-1, 1)
        self.efficiency = (self.velocity * self.torque)
        self.motor = motor
        self.interface = interface or DynoInterface()
        self.power_limit = None
        self.clear()
        if self.logfile:
            self.logfile.write('v: %f %f %f', vel_min, vel_max, vel_step)
            self.logfile.write('t: %f %f %f', torque_min, torque_max, torque_step)

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
        self.add_efficiency_sample(torque, velocity, efficiency)
        if self.logfile:
            self.logfile.write("d: %f, %f, %f" % (torque, velocity, efficiency))

    def add_efficiency_sample(self, torque, velocity, efficiency):
        # Figure out best index
        t = np.abs(self.torque - torque).argmin()
        v = np.abs(self.velocity - velocity).argmin()
        if np.isnan(self.efficiency[t][v]) or efficiency > self.efficiency[t][v]:
            self.efficiency[t][v] = efficiency

    def set_power_limit(self, limit):
        self.power_limit = limit

    def run(self):
        for v in self.velocity:
            print("Setting motor velocity to %f" % v)
            for t in self.torque:
                if self.power_limit and v * t > self.power_limit:
                    continue
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

    def load_from_file(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                if line[0:2] == 'v:':
                    vel_min, vel_max, vel_step = [float(d) for d in line[2:].split(',')]
                    self.velocity = np.arange(vel_min, vel_max + vel_step, vel_step)
                elif line[0:2] == 't:':
                    torque_min, torque_max, torque_step = [float(d) for d in line[2:].split(',')]
                    self.torque = np.arange(torque_min, torque_max + torque_step, torque_step).reshape(-1, 1)
                    self.efficiency = (self.velocity * self.torque)
                    self.clear()
                elif line[0:2] == 'd:':
                    torque, velocity, efficiency = [float(d) for d in line[2:].split(',')]
                    self.add_efficiency_sample(torque, velocity, efficiency)

    def interpolate(self):
        for t_idx, t in enumerate(self.torque):
            for v_idx, v in enumerate(self.velocity):
                if np.isnan(self.efficiency[t_idx][v_idx]):
                    try:
                        self.efficiency[t_idx][v_idx] = self.efficiency[t_idx - 1][v_idx] / 2 + \
                                                        self.efficiency[t_idx + 1][v_idx] / 2
                    except IndexError:
                        pass
                    if not np.isnan(self.efficiency[t_idx][v_idx]):
                        continue
                    try:
                        self.efficiency[t_idx][v_idx] = self.efficiency[t_idx + 1][v_idx]
                    except IndexError:
                        pass
                    if not np.isnan(self.efficiency[t_idx][v_idx]):
                        continue


if __name__ == '__main__':
    e = EfficiencyMap()
    e.load_from_file(sys.argv[1])
    e.interpolate()
    title = 'Motor Efficiency'
    if len(sys.argv) > 2:
        title += 'for ' + sys.argv[2]
    e.plot(title)

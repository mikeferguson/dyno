#!/usr/bin/env python3

# Copyright 2019-2024 Michael Ferguson
# All Rights Reserved

# Dyno software

import socket
import struct
import time

def sign(x):
    if x >= 0:
        return 1
    return -1


## @brief Interface to the Dyno Board
class DynoBoardInterface:

    data_format = "<Iffffff"
    data_names = ["system_time", "system_voltage", "buck_voltage", "buck_current", "torque", "position", "velocity"]

    def __init__(self, ip="192.168.0.43", port=5000):
        self._ip = ip
        self._port = port

        self._conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._conn.bind(("", 0))
        self._conn.setblocking(0)

        self.data_last = [0.0 for var in self.data_names]

    ## @brief Decode a returned packet
    def decode(self, packet):
        if len(packet) != 32:
            print("Invalid packet, insufficient length: %d" % len(packet))
            return None
        if packet[0:4] != b"DYNO":
            print("Invalid packet, header is missing!")
            return None
        values =  struct.unpack(self.data_format,packet[4:])
        return values

    ## @brief Send an update, get a return.
    ## @param absorber_speed Desired absorber speed in rad/s
    ## @param buck_voltage Desired buck voltage command
    ## @param dut_485 Bytes to send to RS-485 DUT interface
    ## @param dut_485_baud Baud rate to set RS-485 output
    ## @param dut_analog_out Voltage level to set analog output to
    ## @returns tuple of values, in same order as data_format
    def update(self, absorber_speed=None, buck_voltage=None,
               dut_485=None, dut_485_baud=None, dut_analog_out=None,
               command_addon = None, timeout=0.1):
        # This is the base command, it gets a return packet of values
        command = b"DYNO"

        # These are optional commands
        if absorber_speed != None:
            command += self.getAbsorberCommand(absorber_speed)

        if buck_voltage != None:
            command += self.getBuckCommand(buck_voltage)

        if dut_485 != None:
            command += self.get485Command(dut_485)

        if dut_485_baud != None:
            command += b"DB" + struct.pack("<H", dut_485_baud)

        if dut_analog_out != None:
            command += self.getAnalogCommand(dut_analog_out)

        if command_addon != None:
            command += command_addon

        # Send the command(s)
        self._conn.sendto(command, 0, (self._ip, self._port))

        # Get the response
        t = time.time()
        while True:
            try:
                packet = self._conn.recv(1024)
                raw_data = list(self.decode(packet))
                raw_data[4] *= -1.0 # Torque is backwards?
                self.data_last = raw_data
                return self.data_last
            except socket.error:
                if time.time() - t > timeout:
                    print("Failed to get return packet!")
                    return None

    ## @brief Sends a stop command (disables absorber and buck)
    def stop(self):
        command = b"DYNOSTOP"
        self._conn.sendto(command, 0, (self._ip, self._port))

    ## @brief Get latest value of a particular variable
    def get(self, variable):
        return self.data_last[self.data_names.index(variable)]

    def getAbsorberCommand(self, absorber_speed):
        return b"S" + struct.pack("<f", absorber_speed)

    def getBuckCommand(self, buck_voltage):
        return b"V" + struct.pack("<f", buck_voltage)

    def get485Command(self, dut_485):
        return b"D4" + struct.pack("<B", len(dut_485)) + dut_485

    def getAnalogCommand(self, dut_analog_out):
        return b"DA" + struct.pack("<f", dut_analog_out)


## @brief Road Load Simulation
##
## Road load is basically modeled as:
##
##   Motor Torque = c0 + c1 * velocity + j * acceleration
##
## The acceleration is then applied to the absorber load,
## which is in velocity-control mode.
class RoadLoad:

    ## @brief Create a RoadLoad simulation instance
    ## @param dyno_interface An instance of DynoBoardInterface
    ## @param j Inertia of the load
    ## @param c0 Constant friction force loss
    ## @param c1 Coefficient for velocity-based force loss
    ## @param use_feedback If true, use velocity from dyno (this can
    ##        lead to a noisy simulation)
    def __init__(self, dyno_interface, j, c0, c1, use_feedback=False):
        self.dyno = dyno_interface
        self.j = j
        self.c0 = c0
        self.c1 = c1
        self.velocity = 0.0
        self.use_feedback = use_feedback
        self.torque_deadband = 0.1

    def getVelocityCommand(self, dt=0.01):
        if abs(self.j) < 0.01:
            # If j is not initialized, don't run updates
            return 0

        torque = self.dyno.get("torque")
        velocity = self.dyno.get("velocity")
        if not self.use_feedback:
            # Open loop control can be less noisy, and is our default
            velocity = self.velocity

        # Deadband on torque
        if abs(torque) < self.torque_deadband:
            torque = 0.0

        # Compute drag friction
        drag_friction = self.c0 + self.c1 * abs(velocity)

        # Compute net torque
        if velocity >= 0:
            net_torque = torque - drag_friction
        else:
            net_torque = torque + drag_friction

        acceleration = net_torque / self.j
        command = velocity + acceleration * dt

        # Friction cannot reverse direction
        if (velocity > 0 and command < 0) or (velocity < 0 and command > 0):
            command = 0.0

        # Store computed velocity
        self.velocity = command
        return command

    def reset(self):
        self.velocity = 0.0


if __name__ == "__main__":
    print()
    print("Dyno Controller v0.1")
    print("Copyright 2019-2024 Michael Ferguson")
    print()

    dyno = DynoBoardInterface()

    print("Test update without commands\n")
    dyno.update()

    print("Test update with commands\n")
    dyno.update(absorber_speed=1.0)

    print("Latest data")
    for data in dyno.data_names:
        print(data + ": " + str(dyno.get(data)))
    print()

    print("Test decoding\n")
    dyno.decode(b"DYN0000000000000000000000000000")
    dyno.decode(b"DYNX0000000000000000000000000000")

    system_time = 1234567
    system_voltage = 12.34
    buck_voltage = 48.48
    buck_current = 1.0
    torque = 0.123
    position = 12425.2
    velocity = 25.0
    packet = b"DYNO"
    packet += struct.pack("<Iffffff", system_time, system_voltage, buck_voltage, buck_current, torque, position, velocity)
    print(dyno.decode(packet))

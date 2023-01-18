#!/usr/bin/env python3

# Copyright 2019-2023 Michael Ferguson
# All Rights Reserved

# Dyno software

import socket
import struct
import time

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
               timeout=0.1):
        # This is the base command, it gets a return packet of values
        command = b"DYNO"

        # These are optional commands
        if absorber_speed != None:
            command += b"S" + struct.pack("<f", absorber_speed)

        if buck_voltage != None:
            command += b"V" + struct.pack("<f", buck_voltage)

        if dut_485 != None:
            command += b"D4" + struct.pack("<B", len(dut_485)) + dut_485

        if dut_485_baud != None:
            command += b"DB" + struct.pack("<H", dut_485_baud)

        if dut_analog_out != None:
            command += b"DA" + struct.pack("<f", dut_analog_out)

        # Send the command(s)
        self._conn.sendto(command, 0, (self._ip, self._port))

        # Get the response
        t = time.time()
        while True:
            try:
                packet = self._conn.recv(1024)
                self.data_last = self.decode(packet)
                return self.data_last
            except socket.error:
                if time.time() - t > timeout:
                    print("Failed to get return packet!")
                    return None

    ## @brief Sends a stop command (disables absorber and buck)
    def stop(self):
        command = b"DYNOSTOP"
        self._conn.sendto(command, 0, (self._ip, self._port))

    ## @brief
    def get(self, variable):
        return self.data_last[self.data_names.index(variable)]


if __name__ == "__main__":
    print()
    print("Dyno Controller v0.1")
    print("Copyright 2019-2023 Michael Ferguson")
    print()

    dyno = DynoBoardInterface()

    print("Test update without commands")
    dyno.update()

    print("Test update with commands")
    dyno.update(absorber_speed=1.0)

    print("Test decoding")
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

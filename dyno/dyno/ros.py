# Copyright 2024 Michael Ferguson
# All Rights Reserved

# Dyno ROS 2 Interface

import rclpy
import threading
from dyno_msgs.msg import LoadSettings, Sample
from dyno_msgs.srv import Trigger


class DynoROS2:

    def __init__(self):
        self.gui = None

        rclpy.init()
        self.node = rclpy.create_node('dyno')
        self.sample_publisher = self.node.create_publisher(Sample, 'dyno/sample', 10)
        self.load_settings_subscriber = self.node.create_subscription(LoadSettings, 'dyno/load_settings', self.load_settings_callback, 10)
        self.trigger_service = self.node.create_service(Trigger, 'dyno/trigger', self.trigger_callback)

        # Start thread
        self.is_shutdown = False
        self.thread = threading.Thread(target = self.spin)
        self.thread.start()

    def spin(self):
        while not self.is_shutdown and rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0.1)

    def shutdown(self):
        self.is_shutdown = True
        self.thread.join()
        self.node.destroy_node()
        rclpy.shutdown()

    def publish(self, st, sv, bv, bc, t, p, v):
        msg = Sample()
        msg.system_time = st
        msg.system_voltage = sv
        msg.buck_voltage = bv
        msg.buck_current = bc
        msg.torque = t
        msg.position = p
        msg.velocity = v
        self.sample_publisher.publish(msg)

    def trigger_callback(self, request, response):
        if self.gui:
            if request.enable:
                self.gui.start_capture()
            else:
                self.gui.stop_capture()
            response.enabled = request.enable
        else:
            response.enabled = False
        return response

    def load_settings_callback(self, msg):
        if self.gui:
            self.gui.absorber_desired_torque.setValue(msg.torque)
            self.gui.absorber_manual_torque.setChecked(True)

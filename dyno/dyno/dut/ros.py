import rclpy
import threading
from dyno_msgs.msg import LoadSettings, Sample
from dyno_msgs.srv import Trigger


"""
Intended to be used for an external test harness that is interacting with
the dyno via the ROS interface.
"""
class DynoInterface:

    def __init__(self, name='dyno_test_harness', run_filter=True):
        rclpy.init()
        self.node = rclpy.create_node(name)
        self.run_filter = run_filter

        # Subscribe to dyno data
        self.latest_data = Sample()
        self.sample_sub = self.node.create_subscription(Sample, 'dyno/sample', self.sample_callback, 10)
        self.load_pub = self.node.create_publisher(LoadSettings, 'dyno/load_settings', 10)

        # TODO: Service to start/stop dyno capture

        # Start spin thread
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

    def sample_callback(self, msg):
        # TODO: lock this?
        if self.run_filter:
            self.latest_data.system_time = msg.system_time
            self.latest_data.system_voltage = msg.system_voltage
            # These are somewhat noisy
            self.latest_data.buck_voltage = 0.9 * self.latest_data.buck_voltage + 0.1 * msg.buck_voltage
            self.latest_data.buck_current = 0.9 * self.latest_data.buck_current + 0.1 * msg.buck_current
            # These are less noisy
            self.latest_data.torque = 0.7 * self.latest_data.torque + 0.3 * msg.torque
            self.latest_data.velocity = 0.7 * self.latest_data.velocity + 0.3 * msg.velocity
            self.latest_data.position = msg.position
        else:
            self.latest_data = msg

    def get_data(self):
        # TODO: lock and return a copy?
        return self.latest_data

    def set_load_torque(self, torque):
        msg = LoadSettings()
        msg.torque = float(torque)
        self.load_pub.publish(msg)

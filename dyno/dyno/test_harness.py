import rclpy
import threading
from dyno_msgs.msg import Sample
from dyno_msgs.srv import Trigger


"""
Intended to be used for an external test harness that is interacting with
the dyno via the ROS interface.
"""
class DynoInterface:

	def __init__(self, name='dyno_test_harness'):
		rclpy.init()
		self.node = rclpy.create_node(name)

        # Subscribe to dyno data
        self.latest_data = Sample()
        self.sub = self.node.create_subscription(Sample, 'dyno/sample', self.sample_callback, 10)

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
        self.latest_data = msg

    def get_data(self):
        # TODO: lock and return a copy?
        return self.latest_data

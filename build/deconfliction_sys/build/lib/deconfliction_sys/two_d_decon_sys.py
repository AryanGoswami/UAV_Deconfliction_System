#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, SetPen
from functools import partial
import math

class TurtleDeconflictionNode(Node):

    def __init__(self):
        super().__init__("turtle_deconfliction")

        # Previous positions for color change
        self.previous_x_turtle1 = 0.0
        self.previous_y_turtle1 = 0.0
        self.previous_x_turtle2 = 0.0
        self.previous_y_turtle2 = 0.0

        # Pose storage for conflict detection
        self.turtle1_pose = None
        self.turtle2_pose = None

        # Publishers for velocity control
        self.turtle1_vel_pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.turtle2_vel_pub = self.create_publisher(Twist, "/turtle2/cmd_vel", 10)

        # Subscribers to track positions
        self.turtle1_pose_sub = self.create_subscription(Pose, "/turtle1/pose", self.pose_callback_turtle1, 10)
        self.turtle2_pose_sub = self.create_subscription(Pose, "/turtle2/pose", self.pose_callback_turtle2, 10)

        # Spawn another turtle
        self.spawn_turtle("turtle2", 3.0, 3.0, 0.0)

        self.get_logger().info("Turtle Deconfliction Node Started!")

    def spawn_turtle(self, name, x, y, theta):
        """Spawns a new turtle at the given location."""
        client = self.create_client(Spawn, "/spawn")
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Waiting for spawn service...")

        request = Spawn.Request()
        request.x = x
        request.y = y
        request.theta = theta
        request.name = name

        future = client.call_async(request)
        future.add_done_callback(partial(self.spawn_callback, name))

    def spawn_callback(self, name, future):
        """Logs spawn completion."""
        try:
            response = future.result()
            self.get_logger().info(f"Turtle '{name}' spawned successfully!")
        except Exception as e:
            self.get_logger().error(f"Spawn failed: {e}")

    def pose_callback_turtle1(self, pose: Pose):
        """Handles position updates for Turtle 1."""
        self.turtle1_pose = pose
        self.move_turtle("turtle1", pose)
        self.check_collision()

    def pose_callback_turtle2(self, pose: Pose):
        """Handles position updates for Turtle 2."""
        self.turtle2_pose = pose
        self.move_turtle("turtle2", pose)
        self.check_collision()

    def move_turtle(self, turtle_name, pose):
        """Moves turtles and avoids boundaries."""
        cmd = Twist()
        if pose.x > 9.0 or pose.x < 2.0 or pose.y > 9.0 or pose.y < 2.0:
            cmd.linear.x = 1.0
            cmd.angular.z = 0.9  # Turn if near the boundary
        else:
            cmd.linear.x = 2.0
            cmd.angular.z = 0.0  # Move forward normally

        if turtle_name == "turtle1":
            self.previous_x_turtle1, self.previous_y_turtle1 = pose.x, pose.y
            self.turtle1_vel_pub.publish(cmd)
        elif turtle_name == "turtle2":
            self.previous_x_turtle2, self.previous_y_turtle2 = pose.x, pose.y
            self.turtle2_vel_pub.publish(cmd)

    def check_collision(self):
        """Detects and prevents turtles from colliding."""
        if self.turtle1_pose and self.turtle2_pose:
            # Euclidean distance between turtles
            distance = math.sqrt((self.turtle1_pose.x - self.turtle2_pose.x) ** 2 + 
                                 (self.turtle1_pose.y - self.turtle2_pose.y) ** 2)

            if distance < 1.0:  # Collision threshold
                self.get_logger().warn("Collision Detected! Adjusting turtles...")
                self.avoid_collision()

    def avoid_collision(self):
        """Stops one turtle and allows the other to move away."""
        stop_cmd = Twist()
        stop_cmd.linear.x = 0.0  # Stop movement

        move_cmd = Twist()
        move_cmd.linear.x = 2.0  # Move forward

        # Stop turtle 1, allow turtle 2 to move
        self.turtle1_vel_pub.publish(stop_cmd)
        self.turtle2_vel_pub.publish(move_cmd)

    def call_set_pen_service(self, turtle_name, r, g, b, width, off):
        """Changes the pen color of a turtle."""
        client = self.create_client(SetPen, f"/{turtle_name}/set_pen")
        while not client.wait_for_service(1.0):
            self.get_logger().warn(f"Waiting for {turtle_name}'s pen service...")

        request = SetPen.Request()
        request.r = r
        request.g = g
        request.b = b
        request.width = width
        request.off = off

        future = client.call_async(request)
        future.add_done_callback(partial(self.callback_set_pen))

    def callback_set_pen(self, future):
        """Handles set_pen service response."""
        try:
            response = future.result()
        except Exception as e:
            self.get_logger().error("Service call failed: %r" % (e,))

def main(args=None):
    """Main function to run the node."""
    rclpy.init(args=args)
    node = TurtleDeconflictionNode()
    rclpy.spin(node)
    rclpy.shutdown()
